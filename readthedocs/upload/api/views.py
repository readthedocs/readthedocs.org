import structlog
from django.conf import settings
from django.core.files.storage import storages
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v3.serializers import BuildSerializer
from readthedocs.api.v3.serializers import VersionSerializer
from readthedocs.api.v3.views import APIv3Settings
from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import BUILD_STATUS_PENDING
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.builds.tasks import send_build_status
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import cancel_build
from readthedocs.core.utils import submit_to_isolated_builders
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.upload.api.serializers import UploadCompleteSerializer
from readthedocs.upload.api.serializers import UploadInitiateSerializer
from readthedocs.upload.api.serializers import UploadStatus


log = structlog.get_logger(__name__)


class UploadInitiateView(APIv3Settings, APIView):
    """
    Initiate a direct artifacts upload.

    Creates a build object in "triggered" state and returns a presigned URL
    for uploading the artifacts zip file to S3.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_slug = serializer.validated_data["project"]
        version_data = serializer.validated_data["version"]

        project = Project.objects.filter(slug=project_slug).first()
        if not project:
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not AdminPermission.is_admin(request.user, project):
            return Response(
                {"detail": "You do not have admin permission for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not project.has_feature(Feature.ALLOW_DIRECT_ARTIFACTS_UPLOAD):
            return Response(
                {"detail": "Direct artifacts upload is not enabled for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not Project.objects.is_active(project):
            return Response(
                {"detail": "Project is not active."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # We don't want users creating a lot of builds and never uploading them.
        # It may be by error or abuse, this limit is high enough to allow for multiple builds to be triggered,
        # but not too high to allow for abuse.
        pending_uploads_count = project.builds.pending_upload().count()
        if pending_uploads_count >= settings.RTD_UPLOAD_API_MAX_PENDING_UPLOADS:
            return Response(
                {
                    "detail": "Too many pending uploads for this project. Finish or cancel some builds before triggering new ones."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Get or create version
        version_name = version_data["name"]
        version_type = version_data["type"]
        version_commit = version_data["commit"]
        privacy_level = version_data["privacy_level"]
        version = self._get_or_create_version(
            project=project,
            name=version_name,
            version_type=version_type,
            privacy_level=privacy_level,
        )

        build = Build.objects.create(
            project=project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            commit=version_commit,
            is_uploaded=True,
        )

        upload_url = self._generate_upload_url(build)

        send_build_status.delay(
            build_pk=build.id,
            commit=version_commit,
            status=BUILD_STATUS_PENDING,
        )

        # Reduce overhead when doing multiple push on the same version.
        running_builds = (
            Build.objects.filter(
                project=project,
                version=version,
            )
            .exclude(
                state__in=BUILD_FINAL_STATES,
            )
            .exclude(
                pk=build.pk,
            )
        )
        running_builds_count = running_builds.count()
        if running_builds_count > 0:
            log.warning(
                "Canceling running builds automatically due a new one arrived.",
                running_builds=running_builds_count,
            )

        # If there are builds triggered/running for this particular project and version,
        # we cancel all of them and trigger a new one for the latest commit received.
        for running_build in running_builds:
            cancel_build(running_build)

        return Response(
            {
                "build": BuildSerializer(build).data,
                "version": VersionSerializer(version).data,
                "upload_url": upload_url,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_or_create_version(self, *, project, name, version_type, privacy_level):
        """Get or create a version for the given project."""
        version = project.versions.filter(verbose_name=name, type=version_type).first()
        if version:
            version.privacy_level = privacy_level
            version.save()
            return version

        version = Version.objects.create(
            project=project,
            verbose_name=name,
            type=version_type,
            identifier=name,
            privacy_level=privacy_level,
            active=True,
        )
        return version

    def _generate_upload_url(self, build):
        """Generate a presigned URL for uploading to S3."""
        storage = storages["build-uploads"]
        response = storage.generate_presigned_post(
            key=build.uploaded_artifacts_storage_path,
            expires_in=settings.RTD_UPLOAD_API_UPLOAD_URL_EXPIRATION_TIME,
            content_type="application/zip",
            max_size=settings.RTD_UPLOAD_API_MAX_UPLOAD_SIZE,
        )
        if settings.RTD_DOCKER_COMPOSE and not settings.USING_AWS:
            # Overriden so we return the public URL for uploading artifacts,
            # instead of the internal hostname (http://storage), which is not accessible from the host machine.
            response["url"] = response["url"].replace("http://storage", "http://127.0.0.1", 1)
        return response


class UploadCompleteView(APIv3Settings, APIView):
    """
    Notify that the upload is complete and trigger build processing.

    This endpoint receives the build ID and status, and triggers
    the processing task if the upload was successful.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        build_id = serializer.validated_data["build"]
        upload_status = serializer.validated_data["status"]

        build = (
            Build.objects.filter(pk=build_id, is_uploaded=True)
            .select_related("project", "version")
            .first()
        )
        if not build:
            return Response(
                {"detail": "Build not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        project = build.project
        if not AdminPermission.is_admin(request.user, project):
            return Response(
                {"detail": "You do not have admin permission for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check build hasn't already been queued for processing.
        if build.task_id or build.state != BUILD_STATE_TRIGGERED:
            return Response(
                {"detail": "Build is already in process."},
                status=status.HTTP_409_CONFLICT,
            )

        # Clean up the build if the upload failed.
        if upload_status == UploadStatus.failed:
            build.state = BUILD_STATE_FINISHED
            build.success = False
            build.save()
            Notification.objects.add(
                message_id=BuildUserError.BUILD_ARTIFACTS_ZIP_UPLOAD_FAILED,
                attached_to=build,
                dismissable=False,
            )
            return Response(
                {"build": BuildSerializer(build).data},
                status=status.HTTP_200_OK,
            )

        storage = storages["build-uploads"]
        if not storage.exists(build.uploaded_artifacts_storage_path):
            return Response(
                {
                    "detail": "Uploaded artifacts file not found in storage. Make sure the upload was successful."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submit_to_isolated_builders(project=project, build=build)

        return Response(
            {"build": BuildSerializer(build).data},
            status=status.HTTP_202_ACCEPTED,
        )
