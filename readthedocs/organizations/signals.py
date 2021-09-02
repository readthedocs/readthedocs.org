"""Organization signals."""

import logging

from allauth.account.signals import user_signed_up
from django.conf import settings
from django.db.models import Count
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build, Version
from readthedocs.builds.signals import build_complete
from readthedocs.organizations.models import (
    Organization,
    Team,
    TeamInvite,
    TeamMember,
)
from readthedocs.projects.models import Project

from .tasks import mark_organization_assets_not_cleaned as mark_organization_assets_not_cleaned_task

log = logging.getLogger(__name__)


@receiver(post_save, sender=Organization)
def sync_org_owners(sender, **kwargs):
    org = kwargs['instance']
    projects = org.projects.all()
    for project in projects:
        project.users.clear()
        for org_owner in org.owners.all():
            project.users.add(org_owner)


@receiver(post_save, sender=Project)
def sync_project_owners(sender, **kwargs):
    """
    Hack to sync organization owners as project users.

    Project users is the readthedocs.org nomenclature for users associated with
    a project. Because projects are organization owned, there should be no users
    outside the projects organization allowed ownership. With each save, clear
    the list of project users and re-add all owners of the organization.

    Projects without owning organizations, which should not exist on
    readthedocs.com, will be orphaned, but not removed.
    """
    if not settings.RTD_ALLOW_ORGANIZATIONS:
        return

    project = kwargs['instance']
    orgs = project.organizations.all()
    if orgs.count():
        log.info(
            'Syncing organization owners to project users for %s',
            project.name,
        )
        org = orgs[0]
        project.users.clear()
        for org_owner in org.owners.all():
            project.users.add(org_owner)
    else:
        log.warning(
            'Syncing organization %s failed. No organizations',
            project.name,
        )


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


@receiver(build_complete, sender=Build)
def mark_organization_assets_not_cleaned(sender, build, **kwargs):
    """
    Mark the organization assets as not cleaned if there is a new build.

    This signal triggers a Celery task because the `build_complete` signal is
    fired by the builder and it does not have access to the database. So, we
    trigger a Celery task that will be executed in the web and mark the
    organization assets as not cleaned.
    """
    if build['state'] == BUILD_STATE_FINISHED:
        mark_organization_assets_not_cleaned_task.delay(build['id'])
