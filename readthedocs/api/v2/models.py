from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager

from readthedocs.projects.models import Project


class BuildAPIKeyManager(BaseAPIKeyManager):
    # pylint: disable=arguments-differ
    def create_key_for_project(self, project):
        """
        Create a project-scoped API key.

        The returned key can read + write anything under ``project``:
        every ``Build`` / ``Version`` / ``Command`` /
        ``Notification`` associated with the project. Used by the
        legacy ``update_docs_task`` path and the webhook path.

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

    def create_key_for_build(self, build):
        """
        Create a build-scoped API key.

        Same 24h expiry as ``create_key_for_project``. Difference is
        the ``build`` FK — when set, the API restricts writes to that
        specific Build (and its Version, commands, notifications).
        See ``permissions.HasBuildScopedBuildAPIKey`` and the per-
        viewset ``get_queryset_for_api_key`` branches for the concrete
        rules.

        The narrower scope keeps the token's blast-radius bounded if
        it leaks: an attacker with a build-scoped key can only
        interfere with that one build, not the whole project.

        Used by the isolated-builders dispatcher in
        ``core/utils/__init__.py::_submit_to_isolated_builders``.
        """
        delta = 60 * 60 * 24  # 24h — matches create_key_for_project
        expiry_date = timezone.now() + timedelta(seconds=delta)
        name_max_length = self.model._meta.get_field("name").max_length
        # Include the build pk in the name so it's easy to identify the
        # key in the Django admin / logs. Distinct from a project-scoped
        # key's name (which is just the slug).
        name = f"{build.project.slug}-b{build.pk}"[:name_max_length]
        return super().create_key(
            name=name,
            expiry_date=expiry_date,
            project=build.project,
            build=build,
        )


class BuildAPIKey(AbstractAPIKey):
    """
    API key for securely interacting with the API from the builders.

    Two scopes are supported, driven by the optional ``build`` FK:

    - **Project-scoped** (``build`` is null): the key can read + write
      anything under ``project``. Legacy behavior, used by the
      ``update_docs_task`` path and the webhook path.

    - **Build-scoped** (``build`` is set): the key can read what the
      build needs (Project details, its Version, ``clone_token``,
      SSH deploy key) but writes are restricted to that specific
      Build and its associated Version / commands / notifications.
      Used by the isolated-builders dispatcher.

    Scope enforcement lives in ``permissions.py`` (permission classes
    that gate access by the ``build`` field) and each viewset's
    ``get_queryset_for_api_key`` (queryset narrowing for build-scoped
    keys).
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="build_api_keys",
        help_text=_("Project that this API key grants access to"),
    )

    build = models.ForeignKey(
        "builds.Build",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text=_(
            "Optional. When set, this API key is scoped to a specific "
            "Build — writes are restricted to that Build (and its "
            "Version, commands, notifications). When null, the key "
            "retains project-wide scope (legacy behavior)."
        ),
    )

    objects = BuildAPIKeyManager()

    class Meta(AbstractAPIKey.Meta):
        verbose_name = _("Build API key")
        verbose_name_plural = _("Build API keys")
