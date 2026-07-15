import structlog
from django.conf import settings
from django.core.files.storage import storages
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.models import BuildAPIKey
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
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.upload.tasks import process_uploaded_build

from .serializers import UploadCompleteSerializer
from .serializers import UploadInitiateSerializer


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

        if not project.has_feature(Feature.ALLOW_DIRECT_ARTIFACTS_UPLOAD):
            return Response(
                {"detail": "Direct artifacts upload is not enabled for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not AdminPermission.is_admin(request.user, project):
            return Response(
                {"detail": "You do not have permission to upload to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not Project.objects.is_active(project):
            return Response(
                {"detail": "Project is not active."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create version
        version_name = version_data["name"]
        version_type = version_data["type"]
        version_commit = version_data["commit"]
        privacy_level = version_data["privacy_level"]
        version_slug = version_data.get("slug", "")
        version = self._get_or_create_version(
            project=project,
            name=version_name,
            version_type=version_type,
            slug=version_slug,
            privacy_level=privacy_level,
        )

        # TODO: put a limit on the number of builds that are on the triggered state.
        # We don't want users creating a lot of builds and never uploading them.
        # It may be by erorr or abuse, the limit should be high enough to allow for multiple builds to be triggered,
        # but not too high to allow for abuse.

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

    def _get_or_create_version(self, project, name, version_type, slug, privacy_level):
        """Get or create a version for the given project."""
        if slug:
            version = project.versions.filter(slug=slug).first()
            if version:
                return version

        version = project.versions.filter(verbose_name=name, type=version_type).first()
        if version:
            return version

        version = Version.objects.create(
            project=project,
            verbose_name=name,
            type=version_type,
            identifier=name,
            privacy_level=privacy_level,
            active=True,
            slug=slug,
        )
        return version

    def _generate_upload_url(self, build):
        """Generate a presigned URL for uploading to S3."""
        storage = storages["build-uploads"]
        response = storage.generate_presigned_post(
            key=build.uploaded_artifacts_storage_path,
            # 30 minutes in seconds
            expires_in=60 * 30,
            content_type="application/zip",
            # 1GB in bytes
            max_size=1024 * 1024 * 1024,
        )
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
                {"detail": "You do not have permission for this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check build is still in a valid state for completion
        if build.state != BUILD_STATE_TRIGGERED:
            return Response(
                {"detail": "Build is already in process."},
                status=status.HTTP_409_CONFLICT,
            )

        # Clean up
        if upload_status == "failed":
            # NOTE: attach a notification about the build failing
            # because the upload didn't complete/failed.
            build.state = BUILD_STATE_FINISHED
            build.success = False
            build.save()
            return Response(
                {"build": BuildSerializer(build).data},
                status=status.HTTP_200_OK,
            )

        options = {}
        # Start the build in X minutes and mark it as limited
        limit_reached, _, max_concurrent_builds = Build.objects.concurrent(project)
        if limit_reached:
            log.warning(
                "Delaying tasks at trigger step due to concurrency limit.",
            )
            # Delay the start of the build for the build retry delay.
            # We're still triggering the task, but it won't run immediately,
            # and the user will be alerted in the UI from the Error below.
            options["countdown"] = settings.RTD_BUILDS_RETRY_DELAY
            options["max_retries"] = settings.RTD_BUILDS_MAX_RETRIES
            Notification.objects.add(
                message_id=BuildMaxConcurrencyError.LIMIT_REACHED,
                attached_to=build,
                dismissable=False,
                format_values={"limit": max_concurrent_builds},
            )

        # Trigger processing task
        _, build_api_key = BuildAPIKey.objects.create_key(project=project)
        task = process_uploaded_build.apply_async(
            kwargs={
                "build_id": build.id,
                "build_api_key": build_api_key,
            },
            **options,
        )
        build.task_id = task.id
        build.save()
        return Response(
            {"build": BuildSerializer(build).data},
            status=status.HTTP_202_ACCEPTED,
        )
