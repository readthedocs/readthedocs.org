"""Project model QuerySet classes."""

from django.db import models
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.utils.extend import SettingsOverrideObject

from . import constants


class ProjectQuerySetBase(models.QuerySet):

    """Projects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.has_perm('projects.view_project'):
            return self.all()
        if user.is_authenticated:
            user_queryset = user.projects.all()
            queryset = user_queryset | queryset
        return queryset

    def for_user_and_viewer(self, user, viewer):
        """Show projects that a user owns, that another user can see."""
        queryset = self.filter(privacy_level=constants.PUBLIC)
        queryset = self._add_user_repos(queryset, viewer)
        queryset = queryset.filter(users__in=[user])
        return queryset.distinct()

    def for_admin_user(self, user):
        if user.is_authenticated:
            return self.filter(users__in=[user])
        return self.none()

    def public(self, user=None):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        return queryset.distinct()

    def protected(self, user=None):
        queryset = self.filter(
            privacy_level__in=[constants.PUBLIC, constants.PROTECTED],
        )
        if user:
            queryset = self._add_user_repos(queryset, user)
        return queryset.distinct()

    def private(self, user=None):
        queryset = self.filter(privacy_level=constants.PRIVATE)
        if user:
            queryset = self._add_user_repos(queryset, user)
        return queryset.distinct()

    def is_active(self, project):
        """
        Check if the project is active.

        The check consists on,
          * the Project shouldn't be marked as skipped.
          * any of the project's owners is banned.

        :param project: project to be checked
        :type project: readthedocs.projects.models.Project

        :returns: whether or not the project is active
        :rtype: bool
        """
        any_owner_banned = any(u.profile.banned for u in project.users.all())
        if project.skip or any_owner_banned:
            return False

        return True

    def max_concurrent_builds(self, project):
        """
        Return the max concurrent builds allowed for the project.

        Max concurrency build priority:

          - project
          - organization
          - default setting

        :param project: project to be checked
        :type project: readthedocs.projects.models.Project

        :returns: number of max concurrent builds for the project
        :rtype: int
        """
        max_concurrent_organization = None
        organization = project.organizations.first()
        if organization:
            max_concurrent_organization = organization.max_concurrent_builds

        return (
            project.max_concurrent_builds or
            max_concurrent_organization or
            settings.RTD_MAX_CONCURRENT_BUILDS
        )

    def prefetch_latest_build(self):
        """
        Prefetch "latest build" for each project.

        .. note::

            This should come after any filtering.
        """
        from readthedocs.builds.models import Build

        # Prefetch the latest build for each project.
        subquery = Subquery(
            Build.internal.filter(
                project=OuterRef('project_id')
            ).order_by('-date').values_list('id', flat=True)[:1]
        )
        latest_build = Prefetch(
            'builds',
            Build.internal.filter(pk__in=subquery),
            to_attr=self.model.LATEST_BUILD_CACHE,
        )
        return self.prefetch_related(latest_build)

    # Aliases

    def dashboard(self, user):
        """Get the projects for this user including the latest build."""
        return self.for_admin_user(user).prefetch_latest_build()

    def api(self, user=None, detail=True):
        if detail:
            return self.public(user)

        queryset = self.none()
        if user:
            queryset = self._add_user_repos(queryset, user)
        return queryset.distinct()


class ProjectQuerySet(SettingsOverrideObject):
    _default_class = ProjectQuerySetBase
    _override_setting = 'PROJECT_MANAGER'


class RelatedProjectQuerySetBase(models.QuerySet):

    """
    Useful for objects that relate to Project and its permissions.

    Objects get the permissions from the project itself.

    ..note:: This shouldn't be used as a subclass.
    """

    use_for_related_fields = True
    project_field = 'project'

    def _add_user_repos(self, queryset, user=None):
        if user.has_perm('projects.view_project'):
            return self.all()
        if user.is_authenticated:
            projects_pk = user.projects.all().values_list('pk', flat=True)
            kwargs = {f'{self.project_field}__in': projects_pk}
            user_queryset = self.filter(**kwargs)
            queryset = user_queryset | queryset
        return queryset

    def public(self, user=None, project=None):
        kwargs = {'%s__privacy_level' % self.project_field: constants.PUBLIC}
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset.distinct()

    def protected(self, user=None, project=None):
        kwargs = {
            '%s__privacy_level__in' % self.project_field: [
                constants.PUBLIC,
                constants.PROTECTED,
            ],
        }
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset.distinct()

    def private(self, user=None, project=None):
        kwargs = {
            '%s__privacy_level' % self.project_field: constants.PRIVATE,
        }
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset.distinct()

    def api(self, user=None):
        return self.public(user)


class RelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = RelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class ParentRelatedProjectQuerySetBase(RelatedProjectQuerySetBase):
    project_field = 'parent'
    use_for_related_fields = True


class ParentRelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = ParentRelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class ChildRelatedProjectQuerySetBase(RelatedProjectQuerySetBase):
    project_field = 'child'
    use_for_related_fields = True


class ChildRelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = ChildRelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class FeatureQuerySet(models.QuerySet):
    use_for_related_fields = True

    def for_project(self, project):
        return self.filter(
            Q(projects=project) |
            Q(past_default_true=True, add_date__gt=project.pub_date),
            Q(future_default_true=True, add_date__lt=project.pub_date),
        ).distinct()


class HTMLFileQuerySetBase(models.QuerySet):

    def internal(self):
        """
        HTMLFileQuerySet method that only includes internal version html files.

        It will exclude pull request/merge request Version html files from the queries
        and only include BRANCH, TAG, UNKNOWN type Version html files.
        """
        return self.exclude(version__type=EXTERNAL)

    def external(self):
        """
        HTMLFileQuerySet method that only includes external version html files.

        It will only include pull request/merge request Version html files in the queries.
        """
        return self.filter(version__type=EXTERNAL)


class HTMLFileQuerySet(SettingsOverrideObject):
    _default_class = HTMLFileQuerySetBase
