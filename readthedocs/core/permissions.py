"""Objects for User permission checks."""
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.organizations.constants import ADMIN_ACCESS, READ_ONLY_ACCESS


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

        if admin:
            # Project Team Admin
            admin_teams = user.teams.filter(access=ADMIN_ACCESS)
            for team in admin_teams:
                if not cls.has_sso_enabled(team.organization, SSOIntegration.PROVIDER_ALLAUTH):
                    projects |= team.projects.all()

            # Org Admin
            for org in user.owner_organizations.all():
                if not cls.has_sso_enabled(org, SSOIntegration.PROVIDER_ALLAUTH):
                    # Do not grant admin access on projects for owners if the
                    # organization has SSO enabled with Authorization on the provider.
                    projects |= org.projects.all()

            projects |= cls._get_projects_for_sso_user(user, admin=True)

        if member:
            # Project Team Member
            member_teams = user.teams.filter(access=READ_ONLY_ACCESS)
            for team in member_teams:
                if not cls.has_sso_enabled(team.organization, SSOIntegration.PROVIDER_ALLAUTH):
                    projects |= team.projects.all()

            projects |= cls._get_projects_for_sso_user(user, admin=False)

        return projects

    @classmethod
    def has_sso_enabled(cls, obj, provider=None):
        return False

    @classmethod
    def _get_projects_for_sso_user(cls, user, admin=False):
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
    def members(cls, obj):
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            return obj.users.all()

        if isinstance(obj, Organization):
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
