"""Build and Version QuerySet classes."""

import datetime

import structlog
from django.db import models
from django.db.models import Q
from django.utils import timezone

from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


__all__ = ["VersionQuerySet", "BuildQuerySet", "RelatedBuildQuerySet"]


class VersionQuerySetBase(NoReprQuerySet, models.QuerySet):
    """Versions take into account their own privacy_level setting."""

    use_for_related_fields = True

    def __init__(self, *args, internal_only=False, external_only=False, **kwargs):
        """
        Overridden to pass extra arguments from the manager.

        Usage:

          import functools

          ManagerClass.from_queryset(
              functools.partial(VersionQuerySet, internal_only=True)
          )

        :param bool internal_only: If this queryset is being used to query internal versions only.
        :param bool external_only: If this queryset is being used to query external versions only.
        """
        self.internal_only = internal_only
        self.external_only = external_only
        super().__init__(*args, **kwargs)

    def _add_from_user_projects(self, queryset, user, admin=False, member=False):
        """Add related objects from projects where `user` is an `admin` or a `member`."""
        if user and user.is_authenticated:
            projects_pk = AdminPermission.projects(
                user=user,
                admin=admin,
                member=member,
            ).values_list("pk", flat=True)
            user_queryset = self.filter(project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset

    def _public_only(self):
        if self.internal_only:
            # Since internal versions are already filtered,
            # don't do anything special.
            queryset = self.filter(privacy_level=constants.PUBLIC)
        elif self.external_only:
            # Since external versions are already filtered,
            # don't filter them again.
            queryset = self.filter(
                project__external_builds_privacy_level=constants.PUBLIC,
            )
        else:
            queryset = self.filter(privacy_level=constants.PUBLIC).exclude(type=EXTERNAL)
            queryset |= self.filter(
                type=EXTERNAL,
                project__external_builds_privacy_level=constants.PUBLIC,
            )
        return queryset

    def public(
        self,
        user=None,
        only_active=True,
        include_hidden=True,
        only_built=False,
    ):
        """
        Get all allowed versions.

        .. note::

           External versions use the `Project.external_builds_privacy_level`
           field instead of its `privacy_level` field.

        .. note::

           Avoid filtering by reverse relationships in this method (like project),
           and instead use project.builds or similar, so the same object is shared
           between the results.
        """
        queryset = self._public_only()
        if user:
            if user.is_superuser:
                queryset = self.all()
            else:
                queryset = self._add_from_user_projects(queryset, user, admin=True, member=True)
        if only_active:
            queryset = queryset.filter(active=True)
        if only_built:
            queryset = queryset.filter(built=True)
        if not include_hidden:
            queryset = queryset.filter(hidden=False)
        return queryset.distinct()

    def api(self, user=None):
        return self.public(user, only_active=False)

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)

    def for_reindex(self):
        """
        Get all versions that can be reindexed.

        A version can be reindexed if:

        - It's active and has been built at least once successfully.
          Since that means that it has files to be indexed.
        - Its project is not delisted or marked as spam.
        - Its project has search indexing enabled.
        """
        return (
            self.filter(
                active=True,
                built=True,
                builds__state=BUILD_STATE_FINISHED,
                builds__success=True,
                project__search_indexing_enabled=True,
            )
            .exclude(project__delisted=True)
            .exclude(project__is_spam=True)
            .distinct()
        )


class VersionQuerySet(SettingsOverrideObject):
    _default_class = VersionQuerySetBase


class BuildQuerySet(NoReprQuerySet, models.QuerySet):
    """
    Build objects that are privacy aware.

    i.e. they take into account the privacy of the Version that they relate to.
    """

    use_for_related_fields = True

    def _add_from_user_projects(self, queryset, user, admin=False, member=False):
        """Add related objects from projects where `user` is an `admin` or a `member`."""
        if user and user.is_authenticated:
            projects_pk = AdminPermission.projects(
                user=user,
                admin=admin,
                member=member,
            ).values_list("pk", flat=True)
            user_queryset = self.filter(project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset

    def public(self, user=None, project=None):
        """
        Get all allowed builds.

        Builds are public if the linked version and project are public.

        .. note::

           External versions use the `Project.external_builds_privacy_level`
           field instead of its `privacy_level` field.
        """
        queryset = self.filter(
            version__privacy_level=constants.PUBLIC,
            version__project__privacy_level=constants.PUBLIC,
        ).exclude(version__type=EXTERNAL)
        queryset |= self.filter(
            version__type=EXTERNAL,
            project__external_builds_privacy_level=constants.PUBLIC,
            project__privacy_level=constants.PUBLIC,
        )
        if user:
            if user.is_superuser:
                queryset = self.all()
            else:
                queryset = self._add_from_user_projects(
                    queryset,
                    user,
                    admin=True,
                    member=True,
                )
        if project:
            queryset = queryset.filter(project=project)
        return queryset.distinct()

    def api(self, user=None):
        return self.public(user)

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)

    def concurrent(self, project):
        """
        Check if the max build concurrency for this project was reached.

        - regular project: counts concurrent builds

        - translation: concurrent builds of all the translations + builds of main project

        .. note::

          If the project/translation belongs to an organization, we count all concurrent
          builds for all the projects from the organization.

        :rtype: tuple
        :returns: limit_reached, number of concurrent builds, number of max concurrent
        """
        limit_reached = False
        query = Q(
            project=project,
        )

        if project.main_language_project:
            # Project is a translation, counts all builds of all the translations
            query |= Q(project__main_language_project=project.main_language_project)
            query |= Q(project__slug=project.main_language_project.slug)

        elif project.translations.exists():
            # The project has translations, counts their builds as well
            query |= Q(project__in=project.translations.all())

        # If the project belongs to an organization, count all the projects
        # from this organization as well
        organization = project.organizations.first()
        if organization:
            query |= Q(project__in=organization.projects.all())

        # Limit builds to 5 hours ago to speed up the query
        query &= Q(date__gt=timezone.now() - datetime.timedelta(hours=5))

        concurrent = (
            (
                self.filter(query).exclude(
                    state__in=[
                        BUILD_STATE_TRIGGERED,
                        BUILD_STATE_FINISHED,
                        BUILD_STATE_CANCELLED,
                    ]
                )
            )
            .distinct()
            .count()
        )

        max_concurrent = Project.objects.max_concurrent_builds(project)
        log.info(
            "Concurrent builds.",
            project_slug=project.slug,
            concurrent=concurrent,
            max_concurrent=max_concurrent,
        )
        if concurrent >= max_concurrent:
            limit_reached = True
        return (limit_reached, concurrent, max_concurrent)


class RelatedBuildQuerySet(NoReprQuerySet, models.QuerySet):
    """
    For models with association to a project through :py:class:`Build`.

    .. note::

       This is only used for ``BuildCommandViewSet`` from api v2.
       Which is being used to upload build command results from the builders.
    """

    use_for_related_fields = True

    def _add_from_user_projects(self, queryset, user):
        if user and user.is_authenticated:
            projects_pk = AdminPermission.projects(
                user=user,
                admin=True,
                member=True,
            ).values_list("pk", flat=True)
            user_queryset = self.filter(build__project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset

    def public(self, user=None):
        queryset = self.filter(build__version__privacy_level=constants.PUBLIC)
        if user:
            if user.is_superuser:
                queryset = self.all()
            else:
                queryset = self._add_from_user_projects(queryset, user)
        return queryset.distinct()

    def api(self, user=None):
        return self.public(user)

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)
