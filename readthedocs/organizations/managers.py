"""Organizations managers."""

from django.db import models

from .constants import ADMIN_ACCESS, READ_ONLY_ACCESS


class RelatedOrganizationManager(models.Manager):

    """Manager to control access."""

    # pylint: disable=unused-argument
    def _add_user_repos(self, queryset, user=None, admin=False, member=False):
        from .models import Organization  # pylint: disable=cyclic-import
        organizations = Organization.objects.for_user(user)
        queryset = self.get_queryset().filter(organization__in=organizations)
        return queryset

    def for_admin_user(self, user):
        projects = self.get_queryset().none()
        return self._add_user_repos(projects, user, admin=True, member=False)

    def for_user(self, user=None, include_all=False):
        queryset = self.get_queryset().none()
        if user and user.is_authenticated:
            if user.is_superuser and include_all:
                return self.get_queryset().all()

            return self._add_user_repos(
                queryset,
                user,
                admin=True,
                member=True,
            )
        return queryset

    def api(self, user=None):
        if user and user.is_superuser:
            return self.public(user=user, include_all=True)
        return self._add_user_repos(
            self.get_queryset(),
            user=user,
            admin=True,
            member=True,
        )


class TeamManager(models.Manager):

    """Manager to control team's access."""

    # pylint: disable=no-self-use
    def teams_for_user(self, user, organization, admin, member):
        from .models import Team  # pylint: disable=cyclic-import
        teams = Team.objects.none()
        if admin:
            # Project Team Admin
            teams |= user.teams.filter(access=ADMIN_ACCESS)

            # Org Admin
            for org in user.owner_organizations.all():
                teams |= org.teams.all()

        if member:
            # Project Team Member
            teams |= user.teams.filter(access=READ_ONLY_ACCESS)

        if organization:
            teams = teams.filter(organization=organization)

        return teams.distinct()

    # pylint: disable=unused-argument
    def public(self, user=None, organization=None, only_active=True):
        queryset = self.get_queryset().all()
        if only_active:
            queryset = queryset.filter(active=True)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset

    def api(self, user=None):
        if user and user.is_superuser:
            return self.public(user)
        return self.teams_for_user(
            user,
            organization=None,
            admin=True,
            member=True,
        )

    def admin(self, user, organization=None, include_all=False):
        if user.is_superuser and include_all:
            return self.get_queryset().all()

        return self.teams_for_user(
            user,
            organization,
            admin=True,
            member=False,
        )

    def member(self, user, organization=None, include_all=False):
        if user.is_superuser and include_all:
            return self.get_queryset().all()

        return self.teams_for_user(
            user,
            organization,
            admin=True,
            member=True,
        )


class TeamMemberManager(models.Manager):

    """Manager for queries on team members."""

    def sorted(self):
        """
        Return sorted list of members and invites.

        Return list of members and invites sorted by members first, and null
        members (invites) last.
        """
        return (
            self.get_queryset().annotate(
                null_member=models.Count('member'),
            ).order_by('-null_member', 'member')
        )
