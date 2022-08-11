"""Organizations managers."""
from django.conf import settings
from django.db import models

from readthedocs.core.utils.extend import SettingsOverrideObject

from .constants import ADMIN_ACCESS, READ_ONLY_ACCESS


class TeamManagerBase(models.Manager):

    """Manager to control team's access."""

    def teams_for_user(self, user, organization, admin, member):
        """Get the teams where the user is an admin or member."""
        teams = self.get_queryset().none()

        if not user.is_authenticated:
            return teams

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

    def public(self, user):
        """
        Return all teams the user has access to.

        If ``ALLOW_PRIVATE_REPOS`` is `False`, all teams are public by default.
        Otherwise, we return only the teams where the user is a member.
        """
        if not settings.ALLOW_PRIVATE_REPOS:
            return self.get_queryset().all()
        return self.member(user)

    def admin(self, user, organization=None):
        return self.teams_for_user(
            user,
            organization,
            admin=True,
            member=False,
        )

    def member(self, user, organization=None):
        return self.teams_for_user(
            user,
            organization,
            admin=True,
            member=True,
        )


class TeamManager(SettingsOverrideObject):
    _default_class = TeamManagerBase


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
