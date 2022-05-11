"""Project model QuerySet classes."""
from django.conf import settings
from django.db import models
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants


class ProjectQuerySetBase(models.QuerySet):

    """Projects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_user_projects(self, queryset, user, admin=False, member=False):
        """Add projects from where `user` is an `admin` or a `member`."""
        projects = AdminPermission.projects(
            user=user,
            admin=admin,
            member=member,
        )
        return queryset | projects

    def for_user_and_viewer(self, user, viewer):
        """
        Show projects that a user owns, that another user can see.

        This includes:

        - Projects where both are member
        - Public projects from `user`
        """
        viewer_projects = self._add_user_projects(self.none(), viewer, admin=True, member=True)
        owner_projects = self._add_user_projects(self.none(), user, admin=True, member=True)
        owner_public_projects = owner_projects.filter(privacy_level=constants.PUBLIC)
        queryset = (viewer_projects & owner_projects) | owner_public_projects
        return queryset.distinct()

    def for_admin_user(self, user):
        queryset = self._add_user_projects(self.none(), user, admin=True, member=False)
        return queryset.distinct()

    def public(self, user=None):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            if user.is_superuser:
                queryset = self.all()
            else:
                queryset = self._add_user_projects(
                    queryset=queryset,
                    user=user,
                    admin=True,
                    member=True,
                )
        return queryset.distinct()

    def for_user(self, user):
        """Return all projects that an user belongs to."""
        queryset = self._add_user_projects(self.none(), user, admin=True, member=True)
        return queryset.distinct()

    def is_active(self, project):
        """
        Check if the project is active.

        The check consists on:

        * the Project shouldn't be marked as skipped.
        * any of the project's owners shouldn't be banned.
        * the organization associated to the project should not be disabled.

        :param project: project to be checked
        :type project: readthedocs.projects.models.Project

        :returns: whether or not the project is active
        :rtype: bool
        """
        any_owner_banned = any(u.profile.banned for u in project.users.all())
        organization = project.organizations.first()
        if (
            project.skip
            or any_owner_banned
            or (organization and organization.disabled)
        ):
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
        return self.for_user(user).prefetch_latest_build()

    def api(self, user=None):
        return self.public(user)

    def single_owner(self, user):
        """
        Returns projects where `user` is the only owner.

        Projects that belong to organizations aren't included.
        """
        return self.annotate(count_users=Count("users")).filter(
            users=user,
            count_users=1,
            organizations__isnull=True,
        )


class ProjectQuerySet(SettingsOverrideObject):
    _default_class = ProjectQuerySetBase


class RelatedProjectQuerySet(models.QuerySet):

    """
    Useful for objects that relate to Project and its permissions.

    Objects get the permissions from the project itself.

    ..note:: This shouldn't be used as a subclass.
    """

    use_for_related_fields = True
    project_field = 'project'

    def _add_from_user_projects(self, queryset, user):
        if user and user.is_authenticated:
            projects_pk = (
                AdminPermission.projects(
                    user=user,
                    admin=True,
                    member=True,
                )
                .values_list('pk', flat=True)
            )
            kwargs = {f'{self.project_field}__in': projects_pk}
            user_queryset = self.filter(**kwargs)
            queryset = user_queryset | queryset
        return queryset

    def public(self, user=None, project=None):
        kwargs = {f'{self.project_field}__privacy_level': constants.PUBLIC}
        queryset = self.filter(**kwargs)
        if user:
            if user.is_superuser:
                queryset = self.all()
            else:
                queryset = self._add_from_user_projects(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset.distinct()

    def api(self, user=None):
        return self.public(user)


class ParentRelatedProjectQuerySet(RelatedProjectQuerySet):
    project_field = 'parent'
    use_for_related_fields = True


class ChildRelatedProjectQuerySet(RelatedProjectQuerySet):
    project_field = 'child'
    use_for_related_fields = True


class FeatureQuerySet(models.QuerySet):
    use_for_related_fields = True

    def for_project(self, project):
        return self.filter(
            Q(projects=project) |
            Q(default_true=True, add_date__gt=project.pub_date) |
            Q(future_default_true=True, add_date__lte=project.pub_date)
        ).distinct()
