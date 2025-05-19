"""Organization signals."""

import structlog
from allauth.account.signals import user_signed_up
from django.db.models import Count
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from djstripe.enums import SubscriptionStatus

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.organizations.models import TeamMember
from readthedocs.payments.utils import cancel_subscription
from readthedocs.projects.models import Project

from .tasks import mark_organization_assets_not_cleaned as mark_organization_assets_not_cleaned_task


log = structlog.get_logger(__name__)


# pylint: disable=unused-argument
@receiver(user_signed_up)
def attach_org(sender, request, user, **kwargs):
    """Attach invited user to organization."""
    team_slug = request.session.get("team")
    if team_slug:
        team = Team.objects.get(slug=team_slug)
        TeamMember.objects.create(team=team, member=user)


# pylint: disable=unused-argument
@receiver(pre_delete, sender=Organization)
def remove_organization_completely(sender, instance, using, **kwargs):
    """
    Remove Organization leaf-overs.

    This includes:

    - Stripe customer
    - Projects
    - Versions
    - Builds (deleted on cascade)
    - Teams
    - Team Invitations
    - Team Memberships
    - Artifacts (HTML, PDF, etc)
    """
    organization = instance

    stripe_customer = organization.stripe_customer
    if stripe_customer:
        log.info(
            "Canceling subscriptions",
            organization_slug=organization.slug,
            stripe_customer_id=stripe_customer.id,
        )
        for subscription in stripe_customer.subscriptions.exclude(
            status=SubscriptionStatus.canceled
        ):
            cancel_subscription(subscription.id)

    log.info("Removing organization completely", organization_slug=organization.slug)

    # ``Project`` has a ManyToMany relationship with ``Organization``. We need
    # to be sure that the projects we are deleting here belongs only to the
    # organization deleted
    projects = Project.objects.annotate(count_organizations=Count("organizations")).filter(
        organizations__in=[organization], count_organizations=1
    )

    # Granular delete that trigger other complex tasks.
    for project in projects:
        # Triggers a task to remove artifacts from storage.
        project.delete()


@receiver(build_complete, sender=Build)
def mark_organization_assets_not_cleaned(sender, build, **kwargs):
    """
    Mark the organization assets as not cleaned if there is a new build.

    This signal triggers a Celery task because the `build_complete` signal is
    fired by the builder and it does not have access to the database. So, we
    trigger a Celery task that will be executed in the web and mark the
    organization assets as not cleaned.
    """
    if build["state"] in BUILD_FINAL_STATES:
        mark_organization_assets_not_cleaned_task.delay(build["id"])
