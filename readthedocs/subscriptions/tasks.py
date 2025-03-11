"""Organization tasks."""

import datetime

import structlog
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from djstripe import models as djstripe

from readthedocs.builds.models import Build
from readthedocs.core.utils import send_email
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Domain
from readthedocs.projects.models import Project
from readthedocs.subscriptions.notifications import OrganizationDisabledNotification
from readthedocs.subscriptions.notifications import TrialEndingNotification
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def daily_email():
    """Daily email beat task for organization notifications."""
    organizations = OrganizationDisabledNotification.for_organizations().distinct()
    for organization in organizations:
        for owner in organization.owners.all():
            notification = OrganizationDisabledNotification(
                context_object=organization,
                user=owner,
            )
            log.info(
                "Notification sent.",
                recipient=owner,
                organization_slug=organization.slug,
            )
            notification.send()

    for subscription in TrialEndingNotification.for_subscriptions():
        organization = subscription.customer.rtd_organization
        if not organization:
            log.error(
                "Susbscription isn't attached to an organization",
                stripe_subscription_id=subscription.id,
            )
            continue

        for owner in organization.owners.all():
            notification = TrialEndingNotification(
                context_object=organization,
                user=owner,
            )
            log.info(
                "Notification sent.",
                recipient=owner,
                organization_slug=organization.slug,
            )
            notification.send()


@app.task(queue="web")
def weekly_subscription_stats_email(recipients=None):
    """
    Weekly email to communicate stats about subscriptions.

    :param list recipients: List of emails to send the stats to.
    """
    if not recipients:
        log.info("No recipients to send stats to.")
        return

    last_week = timezone.now() - datetime.timedelta(weeks=1)
    yesterday = timezone.now() - datetime.timedelta(days=1)

    projects = Project.objects.filter(pub_date__gte=last_week).count()
    builds = Build.objects.filter(date__gte=last_week).count()
    organizations = Organization.objects.filter(pub_date__gte=last_week).count()
    domains = Domain.objects.filter(created__gte=last_week).count()
    organizations_to_disable = Organization.objects.disable_soon(days=30).count()
    users = User.objects.filter(date_joined__gte=last_week).count()
    subscriptions = (
        djstripe.Subscription.objects.filter(
            created__gte=last_week,
            created__lte=yesterday,
        )
        .values("status", "items__price__product__name")
        .annotate(total_status=Count("status"))
        .order_by("status")
    )
    context = {
        "projects": projects,
        "builds": builds,
        "organizations": organizations,
        "domains": domains,
        "organizations_to_disable": organizations_to_disable,
        "users": users,
        "subscriptions": list(subscriptions),
    }

    log.info("Sending weekly subscription stats email.")
    send_email(
        from_email="Read the Docs <no-reply@readthedocs.com>",
        subject="Weekly subscription stats",
        recipient=recipients[0],
        template="subscriptions/notifications/subscription_stats_email.txt",
        template_html=None,
        context=context,
        # Use ``cc`` here because our ``send_email`` does not accept a list of recipients
        cc=recipients[1:],
    )
