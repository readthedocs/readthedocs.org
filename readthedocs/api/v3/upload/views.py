import structlog
from django.conf import settings
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.builds.constants import (
    BUILD_STATE_CANCELLED,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
)
from readthedocs.builds.models import Build, Version
from readthedocs.builds.version_slug import generate_unique_version_slug
from readthedocs.core.permissions import AdminPermission
from readthedocs.projects.models import Project

from ..serializers import BuildSerializer, VersionSerializer
from .serializers import (
    UploadCompleteSerializer,
    UploadInitiateSerializer,
)
from .tasks import process_uploaded_build

log = structlog.get_logger(__name__)


class UploadInitiateView(APIView):
    """
    Initiate a direct artifacts upload.

    Creates a build object in "triggered" state and returns a presigned URL
    for uploading the artifacts zip file to S3.
    """

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UploadInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version_data = serializer.validated_data["version"]
        project_slug = serializer.validated_data.get("project")

        # Get the project
        if project_slug:
            project = (
                Project.objects.for_admin_user(user=request.user)
                .filter(slug=project_slug)
                .first()
            )
        else:
            return Response(
                {"detail": "Project slug is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not project:
            return Response(
                {"detail": "Project not found or you don't have admin permissions."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check admin permissions
        if not AdminPermission.is_admin(request.user, project):
            return Response(
                {"detail": "You do not have permission to upload to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create version
        version_name = version_data["name"]
        version_type = version_data["type"]
        version_commit = version_data["commit"]
        version_slug = version_data.get("slug", "")
        privacy_level = version_data.get(
            "privacy_level", settings.DEFAULT_VERSION_PRIVACY_LEVEL
        )

        version = self._get_or_create_version(
            project=project,
            name=version_name,
            version_type=version_type,
            slug=version_slug,
            privacy_level=privacy_level,
        )

        # Cancel any in-progress builds for this version
        Build.objects.filter(
            version=version,
        ).exclude(
            state__in=[BUILD_STATE_FINISHED, BUILD_STATE_CANCELLED],
        ).update(
            state=BUILD_STATE_CANCELLED,
            success=False,
        )

        # Create a new build object
        build = Build.objects.create(
            project=project,
            version=version,
            type="html",
            state=BUILD_STATE_TRIGGERED,
            success=True,
            commit=version_commit,
            is_uploaded=True,
        )

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            version_slug=version.slug,
            build_id=build.id,
        )
        log.info("Upload initiated.")

        # Generate presigned URL
        upload_key = f"{project.id}/{build.id}/artifacts.zip"
        upload_url = self._generate_upload_url(upload_key)

        return Response(
            {
                "build": BuildSerializer(build).data,
                "version": VersionSerializer(version).data,
                "upload_url": upload_url,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_or_create_version(self, project, name, version_type, slug, privacy_level):
        """Get or create a version for the given project."""
        # Try to find existing version by slug or name
        if slug:
            version = project.versions.filter(slug=slug).first()
            if version:
                return version

        # Try to find by verbose_name and type
        version = project.versions.filter(verbose_name=name, type=version_type).first()
        if version:
            return version

        # Create new version
        version = Version(
            project=project,
            verbose_name=name,
            type=version_type,
            identifier=name,
            privacy_level=privacy_level,
            active=True,
        )
        if slug:
            version.slug = slug
        else:
            version.slug = generate_unique_version_slug(name, version)
        version.save()

        log.info(
            "Created new version for upload.",
            version_slug=version.slug,
        )
        return version

    def _generate_upload_url(self, key):
        """Generate a presigned URL for uploading to S3."""
        from django.core.files.storage import storages

        try:
            storage = storages["build-uploads"]
            # Check if it's an S3 storage with presigned post support
            if hasattr(storage, "generate_presigned_post"):
                return storage.generate_presigned_post(key=key)
        except Exception:
            log.exception("Failed to generate presigned URL.")

        # Fallback for non-S3 storage (e.g., local dev/test)
        # Return a placeholder that indicates the upload path
        return {
            "url": f"/upload/{key}",
            "fields": {},
        }


class UploadCompleteView(APIView):
    """
    Notify that the upload is complete and trigger build processing.

    This endpoint receives the build ID and status, and triggers
    the processing task if the upload was successful.
    """

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        build_id = serializer.validated_data["build"]
        upload_status = serializer.validated_data["status"]

        # Fetch the build
        try:
            build = Build.objects.get(pk=build_id, is_uploaded=True)
        except Build.DoesNotExist:
            return Response(
                {"detail": "Build not found or is not an uploaded build."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        project = build.project
        if not AdminPermission.is_admin(request.user, project):
            return Response(
                {"detail": "You do not have permission for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check build is still in a valid state for completion
        if build.state in [BUILD_STATE_FINISHED, BUILD_STATE_CANCELLED]:
            return Response(
                {"detail": "Build is already in a final state."},
                status=status.HTTP_409_CONFLICT,
            )

        if upload_status == "failed":
            build.state = BUILD_STATE_FINISHED
            build.success = False
            build.save()
            log.info(
                "Upload marked as failed.",
                build_id=build.id,
            )
            return Response(
                {"build": BuildSerializer(build).data},
                status=status.HTTP_200_OK,
            )

        # Trigger processing task
        process_uploaded_build.delay(build_id=build.id)

        log.info(
            "Upload complete, processing triggered.",
            build_id=build.id,
        )

        return Response(
            {"build": BuildSerializer(build).data},
            status=status.HTTP_202_ACCEPTED,
        )
