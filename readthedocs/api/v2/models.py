from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager

from readthedocs.projects.models import Project


class ProjectAPIKeyManager(BaseAPIKeyManager):
    def create_internal_key(self, project):
        """
        Create a new internal API key for a project, to be used by our builders.

        Build API keys are valid for

        - project or default build time limit
        - plus 25% to cleanup task once build is finished
        - plus extra time to allow multiple retries (concurrency limit reached)

        and can be revoked at any time by hitting the /api/v2/revoke/ endpoint.
        """
        # delta = (
        #     project.container_time_limit or settings.BUILD_TIME_LIMIT
        # ) * 1.25 + settings.RTD_BUILDS_RETRY_DELAY * settings.RTD_BUILDS_MAX_RETRIES
        #
        # Use 24 hours for now since we are hitting the expiry date and we shouldn't
        # https://github.com/readthedocs/readthedocs.org/issues/12467
        #
        # NOTE: this is the maximum time this token will be valid, since the
        # default behavior is to revoke from the builder itself when the build
        # at `after_return` immediately before the build finishes
        delta = 60 * 60 * 24  # 24h
        expiry_date = timezone.now() + timedelta(seconds=delta)
        name_max_length = self.model._meta.get_field("name").max_length
        return self.create_key(
            # Name is required, so we use the project slug for it.
            name=project.slug[:name_max_length],
            expiry_date=expiry_date,
            project=project,
            internal=True,
            permission_level=self.model.PermissionLevel.READ_WRITE,
        )

    def create_project_key(
        self,
        project,
        name,
        expiry_date=None,
        permission_level=None,
        description="",
    ):
        """
        Create a new API key for a project, to be exposed to its admins.

        ``expiry_date`` set to ``None`` means the key never expires.
        """
        permission_level = permission_level or self.model.PermissionLevel.READ_ONLY
        name_max_length = self.model._meta.get_field("name").max_length
        return self.create_key(
            name=name[:name_max_length],
            expiry_date=expiry_date,
            project=project,
            internal=False,
            permission_level=permission_level,
            description=description,
        )


class ProjectAPIKey(AbstractAPIKey):
    """
    API key attached to a single project.

    Internal keys are created for each build and used by the builders to
    interact with the API V2. Non-internal keys are created by project admins
    from the dashboard, and can only interact with the API V3.
    """

    class PermissionLevel(models.TextChoices):
        READ_ONLY = "read_only", _("Read only")
        READ_WRITE = "read_write", _("Read and write")

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text=_("Project that this API key grants access to"),
    )
    # NOTE: ``db_default`` differs from ``default`` on purpose. All keys that
    # existed before these fields were added (or are created by old code while
    # deploying) are builder keys, so the database fills them as internal and
    # read/write. New code has to opt in explicitly, so a forgotten value ends
    # up as the least privileged key.
    internal = models.BooleanField(
        _("Internal"),
        default=False,
        db_default=True,
        help_text=_(
            "Internal keys are used by our builders and grant access to internal endpoints"
        ),
    )
    permission_level = models.CharField(
        _("Permission level"),
        max_length=16,
        choices=PermissionLevel.choices,
        default=PermissionLevel.READ_ONLY,
        db_default=PermissionLevel.READ_WRITE,
        help_text=_("Read only keys can't modify the project in any way"),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        default="",
        db_default="",
        help_text=_("Optional description to remember what this key is used for"),
    )

    objects = ProjectAPIKeyManager()

    class Meta(AbstractAPIKey.Meta):
        # Renamed from ``BuildAPIKey``; the table keeps its original name.
        db_table = "v2_buildapikey"
        verbose_name = _("Project API key")
        verbose_name_plural = _("Project API keys")

    @property
    def is_read_only(self):
        return self.permission_level == self.PermissionLevel.READ_ONLY
