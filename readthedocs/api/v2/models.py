from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager

from readthedocs.projects.models import Project


class BuildAPIKeyManager(BaseAPIKeyManager):
    # pylint: disable=arguments-differ
    def create_key(self, project):
        """
        Create a new API key for a project.

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
        return super().create_key(
            # Name is required, so we use the project slug for it.
            name=project.slug[:name_max_length],
            expiry_date=expiry_date,
            project=project,
        )


class BuildAPIKey(AbstractAPIKey):
    """
    API key for securely interacting with the API from the builders.

    The key is attached to a single project,
    it can be used to have write access to the API V2.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="build_api_keys",
        help_text=_("Project that this API key grants access to"),
    )

    objects = BuildAPIKeyManager()

    class Meta(AbstractAPIKey.Meta):
        verbose_name = _("Build API key")
        verbose_name_plural = _("Build API keys")
