import structlog
from django.conf import settings
from django.core.files.storage import storages
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.utils import run_version_automation_rules
from readthedocs.api.v3.serializers import BuildSerializer
from readthedocs.api.v3.serializers import VersionSerializer
from readthedocs.api.v3.views import APIv3Settings
from readthedocs.audit.models import AuditLog
from readthedocs.audit.serializers import UploadSerializer
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import EXTERNAL_VERSION_STATE_OPEN
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import prepare_build
from readthedocs.core.utils import submit_to_build_isolated
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import MESSAGE_PROJECT_DEFAULT_VERSION_FROM_UPLOAD
from readthedocs.upload.api.serializers import UploadCompleteSerializer
from readthedocs.upload.api.serializers import UploadInitiateSerializer
from readthedocs.upload.api.serializers import UploadStatus


log = structlog.get_logger(__name__)


class UploadAuditMixin:
    """
    Record upload API calls in the security log.

    Uploads are authenticated with API tokens, which never go through the dashboard login,
    so these entries are the only record of who published to a project and from where.
    """

    def _audit_denied(self, project, reason):
        AuditLog.objects.new(
            action=AuditLog.UPLOAD_DENIED,
            user=self.request.user,
            request=self.request,
            project=project,
            data={"reason": reason},
        )

    def _audit_upload(self, action, build, **extra):
        data = UploadSerializer(build).data
        data.update(extra)
        AuditLog.objects.new(
            action=action,
            user=self.request.user,
            request=self.request,
            project=build.project,
            data=data,
        )


class UploadInitiateView(UploadAuditMixin, APIv3Settings, APIView):
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
            self._audit_denied(project, reason="not-admin")
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
        version, created = self._get_or_create_version(
            project=project,
            name=version_name,
            version_type=version_type,
            privacy_level=privacy_level,
        )
        if created:
            self._on_version_created(project=project, version=version)

        _, build = prepare_build(
            project=project, version=version, commit=version_commit, is_uploaded=True
        )

        upload_url = self._generate_upload_url(build)

        self._audit_upload(AuditLog.UPLOAD_INITIATED, build, version_created=created)

        return Response(
            {
                "build": BuildSerializer(build).data,
                "version": VersionSerializer(version).data,
                "upload_url": upload_url,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_or_create_version(self, *, project, name, version_type, privacy_level):
        """
        Get or create a version for the given project.

        If the version already exists, it will be updated with the new privacy level and set to active.

        :returns: a tuple of the version and whether it was created.
        """
        # On projects built by Read the Docs, an upload of the branch or tag that "latest" tracks
        # lands on "latest", the version a push to it builds (see `Project.versions_from_name`).
        # Direct upload projects have no aliases: the uploaded name is the version.
        if not project.is_direct_upload:
            latest = project.get_latest_version()
            if (
                latest
                and latest.machine
                and latest.identifier == name
                and latest.type == version_type
            ):
                latest.privacy_level = privacy_level
                latest.active = True
                latest.save()
                return latest, False

        version = project.versions.filter(verbose_name=name, type=version_type).first()
        if version:
            version.identifier = name
            version.privacy_level = privacy_level
            version.state = EXTERNAL_VERSION_STATE_OPEN
            version.active = True
            version.machine = False
            version.save()
            return version, False

        # A version that only exists because of an upload is uploaded from the start,
        # so nothing (automation rules included) builds it on Read the Docs meanwhile.
        version = Version.objects.create(
            project=project,
            verbose_name=name,
            type=version_type,
            identifier=name,
            privacy_level=privacy_level,
            state=EXTERNAL_VERSION_STATE_OPEN,
            active=True,
            is_uploaded=True,
        )
        return version, True

    def _on_version_created(self, *, project, version):
        """
        Extra steps for a version created by an upload.

        The first branch or tag uploaded to a direct upload project becomes its default version,
        since these projects don't get "latest" automatically,
        and the user is told so they can change it.
        Pull request previews never become the default.

        On projects built by Read the Docs, automation rules run for the new version
        like they do when the repository sync creates one.
        Direct upload projects don't run automation rules for now.
        """
        if project.is_direct_upload:
            if (
                version.type != EXTERNAL
                and not project.versions.filter(slug=project.default_version).exists()
            ):
                project.default_version = version.slug
                project.save(update_fields=["default_version"])
                Notification.objects.add(
                    attached_to=project,
                    message_id=MESSAGE_PROJECT_DEFAULT_VERSION_FROM_UPLOAD,
                    dismissable=True,
                    format_values={"version": version.verbose_name},
                )
            return

        run_version_automation_rules(
            project,
            added_versions={version.slug},
            deleted_active_versions=set(),
        )

    def _generate_upload_url(self, build):
        """Generate a presigned URL for uploading to S3."""
        storage = storages["build-uploads"]
        response = storage.generate_presigned_post(
            key=build.uploaded_artifacts_storage_path,
            expires_in=settings.RTD_UPLOAD_API_UPLOAD_URL_EXPIRATION_TIME,
            content_type="application/zip",
            max_size=build.project.max_build_media_size or settings.RTD_UPLOAD_API_MAX_UPLOAD_SIZE,
        )
        if settings.RTD_DOCKER_COMPOSE and not settings.USING_AWS:
            # Overriden so we return the public URL for uploading artifacts,
            # instead of the internal hostname (http://storage), which is not accessible from the host machine.
            response["url"] = response["url"].replace("://storage", "://127.0.0.1", 1)
        return response


class UploadCompleteView(UploadAuditMixin, APIv3Settings, APIView):
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
            self._audit_denied(project, reason="not-admin")
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

        # Mark the build as finished if the upload failed.
        if upload_status == UploadStatus.failed:
            build.state = BUILD_STATE_FINISHED
            build.success = False
            build.save()
            Notification.objects.add(
                message_id=BuildUserError.BUILD_ARTIFACTS_ZIP_UPLOAD_FAILED,
                attached_to=build,
                dismissable=False,
            )
            self._audit_upload(AuditLog.UPLOAD_COMPLETED, build, status=upload_status)
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

        submit_to_build_isolated(project=project, build=build)

        self._audit_upload(AuditLog.UPLOAD_COMPLETED, build, status=upload_status)

        return Response(
            {"build": BuildSerializer(build).data},
            status=status.HTTP_202_ACCEPTED,
        )
