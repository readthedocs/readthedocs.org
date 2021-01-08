"""Organization signals."""

import logging

from allauth.account.signals import user_signed_up
from django.db.models import Count
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from readthedocs.builds.models import Version
from readthedocs.organizations.models import (
    Organization,
    Team,
    TeamInvite,
    TeamMember,
)
from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


# pylint: disable=unused-argument
@receiver(user_signed_up)
def attach_org(sender, request, user, **kwargs):
    """Attach invited user to organization."""
    team_slug = request.session.get('team')
    if team_slug:
        team = Team.objects.get(slug=team_slug)
        TeamMember.objects.create(team=team, member=user)


# pylint: disable=unused-argument
@receiver(pre_delete, sender=Organization)
def remove_organization_completely(sender, instance, using, **kwargs):
    """
    Remove Organization leaf-overs.

    This includes:

    - Projects
    - Versions
    - Builds (deleted on cascade)
    - Teams
    - Team Invitations
    - Team Memberships
    - Artifacts (HTML, PDF, etc)
    """
    organization = instance
    log.info('Removing Organization %s completely', organization.slug)

    # ``Project`` has a ManyToMany relationship with ``Organization``. We need
    # to be sure that the projects we are deleting here belongs only to the
    # organization deleted
    projects = Project.objects.annotate(
        Count('organizations'),
    ).filter(
        organizations__in=[organization],
        organizations__count=1,
    )

    versions = Version.objects.filter(project__in=projects)
    teams = Team.objects.filter(organization=organization)
    team_invites = TeamInvite.objects.filter(organization=organization)
    team_memberships = TeamMember.objects.filter(team__in=teams)

    # Bulk delete
    team_memberships.delete()
    team_invites.delete()
    teams.delete()

    # Granular delete that trigger other complex tasks
    for version in versions:
        # Triggers a task to remove artifacts from storage
        version.delete()

    projects.delete()
