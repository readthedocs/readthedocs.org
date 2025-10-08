"""Objects for User permission checks."""

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.organizations.constants import ADMIN_ACCESS
from readthedocs.organizations.constants import READ_ONLY_ACCESS


class AdminPermissionBase:
    @classmethod
    def projects(cls, user, admin=False, member=False):
        """
        Return all the projects the user has access to as ``admin`` or ``member``.

        If `RTD_ALLOW_ORGANIZATIONS` is enabled
        This function takes into consideration VCS SSO and Google SSO.
        It includes:

        - projects where the user has access to via VCS SSO.
        - Projects where the user has access via Team,
          if VCS SSO is not enabled for the organization of that team.

        .. note::

           SSO is taken into consideration,
           but isn't implemented in .org yet.

        :param user: user object to filter projects
        :type user: django.contrib.admin.models.User
        :param bool admin: include projects where the user has admin access to the project
        :param bool member: include projects where the user has read access to the project
        """
        from readthedocs.projects.models import Project
        from readthedocs.sso.models import SSOIntegration

        projects = Project.objects.none()
        if not user or not user.is_authenticated:
            return projects

        if not settings.RTD_ALLOW_ORGANIZATIONS:
            # All users are admin and member of a project
            # when we aren't using organizations.
            return user.projects.all()

        projects_from_sso = Project.objects.none()
        projects_from_teams = Project.objects.none()
        projects_from_owners = Project.objects.none()

        if admin or member:
            # Projects from VCS SSO.
            projects_from_sso = cls._get_projects_for_sso_user(user, admin=admin, member=member)

            # Projects from teams that don't have VCS SSO enabled.
            filter = Q()
            if admin:
                filter |= Q(teams__access=ADMIN_ACCESS)
            if member:
                filter |= Q(teams__access=READ_ONLY_ACCESS)
            projects_from_teams = Project.objects.filter(filter, teams__members=user).exclude(
                organizations__ssointegration__provider=SSOIntegration.PROVIDER_ALLAUTH,
            )

        # Projects from organizations that don't have VCS SSO enabled,
        # where the user is an owner.
        if admin:
            projects_from_owners = Project.objects.filter(organizations__owners=user).exclude(
                organizations__ssointegration__provider=SSOIntegration.PROVIDER_ALLAUTH,
            )

        # NOTE: We use a filter with Q objects instead of several union operations
        # (e.g projects_from_sso | projects_from_teams | projects_from_owners),
        # as the latter can generate a very complex and slow query.
        return Project.objects.filter(
            Q(id__in=projects_from_sso)
            | Q(id__in=projects_from_teams)
            | Q(id__in=projects_from_owners)
        )

    @classmethod
    def organizations(cls, user, owner=False, member=False):
        from readthedocs.organizations.models import Organization

        organizations = Organization.objects.none()

        if owner:
            organizations |= Organization.objects.filter(owners__in=[user]).distinct()

        if member:
            organizations |= Organization.objects.filter(
                projects__in=cls.projects(user, admin=True, member=True)
            ).distinct()

        return organizations

    @classmethod
    def has_sso_enabled(cls, obj, provider=None):
        return False

    @classmethod
    def _get_projects_for_sso_user(cls, user, admin=False, member=False):
        from readthedocs.projects.models import Project

        return Project.objects.none()

    @classmethod
    def owners(cls, obj):
        """
        Return the owners of `obj`.

        If organizations are enabled,
        we return the owners of the project organization instead.
        """
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            if settings.RTD_ALLOW_ORGANIZATIONS:
                obj = obj.organizations.first()
            else:
                return obj.users.all()

        if isinstance(obj, Organization):
            return obj.owners.all()

    @classmethod
    def admins(cls, obj):
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            return obj.users.all()

        if isinstance(obj, Organization):
            return obj.owners.all()

    @classmethod
    def members(cls, obj, user=None):
        """
        Return the users that are members of `obj`.

        If `user` is provided, we return the members of `obj` that are visible to `user`.
        For a project this means the users that have access to the project,
        and for an organization, this means the users that are on the same teams as `user`,
        including the organization owners.
        """
        from readthedocs.organizations.models import Organization
        from readthedocs.organizations.models import Team
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            project_owners = obj.users.all()
            if user and user not in project_owners:
                return User.objects.none()
            return project_owners

        if isinstance(obj, Organization):
            if user:
                teams = Team.objects.member(user, organization=obj)
                return User.objects.filter(
                    Q(teams__in=teams) | Q(owner_organizations=obj),
                ).distinct()

            return User.objects.filter(
                Q(teams__organization=obj) | Q(owner_organizations=obj),
            ).distinct()

    @classmethod
    def is_admin(cls, user, obj):
        # This explicitly uses "user in project.users.all" so that
        # users on projects can be cached using prefetch_related or prefetch_related_objects
        return user in cls.admins(obj) or user.is_superuser

    @classmethod
    def is_member(cls, user, obj):
        return user in cls.members(obj) or user.is_superuser


class AdminPermission(SettingsOverrideObject):
    _default_class = AdminPermissionBase
