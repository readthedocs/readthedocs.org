"""Organizations managers."""

from django.db import models

from readthedocs.core.utils.extend import SettingsOverrideObject

from .constants import ADMIN_ACCESS
from .constants import READ_ONLY_ACCESS


class TeamManagerBase(models.Manager):
    """Manager to control team's access."""

    def teams_for_user(self, user, organization, admin, member):
        teams = self.get_queryset().none()
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
            self.get_queryset()
            .annotate(
                null_member=models.Count("member"),
            )
            .order_by("-null_member", "member")
        )
