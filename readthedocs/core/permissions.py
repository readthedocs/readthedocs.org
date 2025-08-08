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

        # Internal cache to avoid hitting the database/cache multiple times.
        organizations_with_allauth_sso = {}
        def _has_sso_enabled(org):
            if org.pk not in organizations_with_allauth_sso:
                organizations_with_allauth_sso[org.pk] = cls.has_sso_enabled(
                    org,
                    SSOIntegration.PROVIDER_ALLAUTH,
                )
            return organizations_with_allauth_sso[org.pk]

        # Projects from teams
        filter = Q()
        if admin:
            filter |= Q(access=ADMIN_ACCESS)
        if member:
            filter |= Q(access=READ_ONLY_ACCESS)

        teams = user.teams.filter(filter).select_related("organization", "organization__ssointegration")
        for team in teams:
            if not _has_sso_enabled(team.organization):
                projects |= team.projects.all()

        if admin:
            # Org Admin
            for org in user.owner_organizations.all():
                if not _has_sso_enabled(org):
                    # Do not grant admin access on projects for owners if the
                    # organization has SSO enabled with Authorization on the provider.
                    projects |= org.projects.all()

            projects |= cls._get_projects_for_sso_user(user, admin=True)

        if member:
            projects |= cls._get_projects_for_sso_user(user, admin=False)

        return projects

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
