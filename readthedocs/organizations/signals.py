"""Organization signals."""

import structlog
from allauth.account.signals import user_signed_up
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from djstripe.enums import SubscriptionStatus

from readthedocs.builds.models import Build
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.organizations.models import TeamMember
from readthedocs.payments.utils import cancel_subscription


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
    Remove Organization leftovers.

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
    # Granular delete that trigger other complex tasks,
    # like remove artifacts from storage.
    for project in organization.projects.all():
        project.delete()


@receiver(post_save, sender=Build)
def mark_organization_assets_not_cleaned(sender, instance, created, **kwargs):
    """Mark the organization assets as not cleaned if there is a new successful build."""
    build = instance
    if build.finished and build.success:
        organization = build.project.organization
        if organization and organization.artifacts_cleaned:
            log.info(
                "Marking organization as not cleaned.",
                origanization_slug=organization.slug,
            )
            organization.artifacts_cleaned = False
            organization.save(update_fields=["artifacts_cleaned"])
