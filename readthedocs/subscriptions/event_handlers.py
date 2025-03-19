"""
Dj-stripe webhook handlers.

https://docs.dj-stripe.dev/en/master/usage/webhooks/.
"""

import requests
import structlog
from django.conf import settings
from django.contrib.humanize.templatetags import humanize
from django.db.models import Sum
from django.utils import timezone
from djstripe import models as djstripe
from djstripe import webhooks
from djstripe.enums import ChargeStatus
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.payments.utils import cancel_subscription as cancel_stripe_subscription
from readthedocs.projects.models import Domain
from readthedocs.sso.models import SSOIntegration
from readthedocs.subscriptions.notifications import SubscriptionEndedNotification
from readthedocs.subscriptions.notifications import SubscriptionRequiredNotification


log = structlog.get_logger(__name__)


def handler(*args, **kwargs):
    """
    Register handlers only if organizations are enabled.

    Wrapper around the djstripe's webhooks.handler decorator,
    to register the handler only if organizations are enabled.
    """

    def decorator(func):
        if settings.RTD_ALLOW_ORGANIZATIONS:
            return webhooks.handler(*args, **kwargs)(func)
        return func

    return decorator


@handler("customer.subscription.created")
def subscription_created_event(event):
    """
    Handle the creation of a new subscription.

    When a new subscription is created, the latest subscription
    of the organization is updated to point to this new subscription.

    If the organization attached to the customer is disabled,
    we re-enable it, since the user just subscribed to a plan.
    """
    stripe_subscription_id = event.data["object"]["id"]
    log.bind(stripe_subscription_id=stripe_subscription_id)

    stripe_subscription = djstripe.Subscription.objects.filter(id=stripe_subscription_id).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return

    organization = getattr(stripe_subscription.customer, "rtd_organization", None)
    if not organization:
        log.error("Subscription isn't attached to an organization")
        return

    if organization.disabled:
        log.info("Re-enabling organization.", organization_slug=organization.slug)
        organization.disabled = False

    old_subscription_id = (
        organization.stripe_subscription.id if organization.stripe_subscription else None
    )
    log.info(
        "Attaching new subscription to organization.",
        organization_slug=organization.slug,
        old_stripe_subscription_id=old_subscription_id,
    )
    organization.stripe_subscription = stripe_subscription
    organization.save()


@handler("customer.subscription.updated", "customer.subscription.deleted")
def subscription_updated_event(event):
    """
    Handle subscription updates.

    We need to cancel trial subscriptions manually when their trial period ends,
    otherwise Stripe will keep them active.

    If the organization attached to the subscription is disabled,
    and the subscription is now active, we re-enable the organization.

    We also re-evaluate the latest subscription attached to the organization,
    in case it changed.
    """
    stripe_subscription_id = event.data["object"]["id"]
    log.bind(stripe_subscription_id=stripe_subscription_id)
    stripe_subscription = djstripe.Subscription.objects.filter(id=stripe_subscription_id).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return

    trial_ended = stripe_subscription.trial_end and stripe_subscription.trial_end < timezone.now()
    is_trial_subscription = stripe_subscription.items.filter(
        price__id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE
    ).exists()
    if (
        is_trial_subscription
        and trial_ended
        and stripe_subscription.status != SubscriptionStatus.canceled
    ):
        log.info(
            "Trial ended, canceling subscription.",
        )
        cancel_stripe_subscription(stripe_subscription.id)
        return

    organization = getattr(stripe_subscription.customer, "rtd_organization", None)
    if not organization:
        log.error("Subscription isn't attached to an organization")
        return

    if stripe_subscription.status == SubscriptionStatus.active and organization.disabled:
        log.info("Re-enabling organization.", organization_slug=organization.slug)
        organization.disabled = False

    if stripe_subscription.status not in (SubscriptionStatus.active, SubscriptionStatus.trialing):
        if organization.never_disable:
            log.info(
                "Organization can't be disabled, skipping deactivation.",
                organization_slug=organization.slug,
            )
        else:
            log.info(
                "Organization disabled due its subscription is not active anymore.",
                organization_slug=organization.slug,
            )
            organization.disabled = True

    new_stripe_subscription = organization.get_stripe_subscription()
    if organization.stripe_subscription != new_stripe_subscription:
        old_subscription_id = (
            organization.stripe_subscription.id if organization.stripe_subscription else None
        )
        log.info(
            "Attaching new subscription to organization.",
            organization_slug=organization.slug,
            old_stripe_subscription_id=old_subscription_id,
        )
        organization.stripe_subscription = new_stripe_subscription

    organization.save()


@handler("customer.subscription.deleted")
def subscription_canceled(event):
    """
    Send a notification to all owners if the subscription has ended.

    We send a different notification if the subscription
    that ended was a "trial subscription",
    since those are from new users.
    """
    stripe_subscription_id = event.data["object"]["id"]
    log.bind(stripe_subscription_id=stripe_subscription_id)
    stripe_subscription = djstripe.Subscription.objects.filter(id=stripe_subscription_id).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return

    total_spent = (
        stripe_subscription.customer.charges.filter(status=ChargeStatus.succeeded)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )
    log.bind(total_spent=total_spent)

    # Using `getattr` to avoid the `RelatedObjectDoesNotExist` exception
    # when the subscription doesn't have an organization attached to it.
    organization = getattr(stripe_subscription.customer, "rtd_organization", None)
    if not organization:
        log.error("Subscription isn't attached to an organization")
        return

    if organization.never_disable:
        log.info(
            "Organization can't be disabled, skipping notification.",
            organization_slug=organization.slug,
        )
        return

    log.bind(organization_slug=organization.slug)
    is_trial_subscription = stripe_subscription.items.filter(
        price__id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE
    ).exists()
    notification_class = (
        SubscriptionRequiredNotification if is_trial_subscription else SubscriptionEndedNotification
    )
    for owner in organization.owners.all():
        notification = notification_class(
            context_object=organization,
            user=owner,
        )
        notification.send()
        log.info(
            "Notification sent.",
            username=owner.username,
            organization_slug=organization.slug,
        )

    if settings.SLACK_WEBHOOK_SALES_CHANNEL and total_spent > 0:
        start_date = stripe_subscription.start_date.strftime("%b %-d, %Y")
        timesince = humanize.naturaltime(stripe_subscription.start_date).split(",")[0]
        domains = Domain.objects.filter(project__organizations__in=[organization]).count()
        try:
            sso_integration = organization.ssointegration.provider
        except SSOIntegration.DoesNotExist:
            sso_integration = "Read the Docs Auth"

        # https://api.slack.com/surfaces/messages#payloads
        slack_message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": ":x: *Subscription canceled*"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f":office: *Name:* <{settings.ADMIN_URL}/organizations/organization/{organization.pk}/change/|{organization.name}>",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f":dollar: *Plan:* <https://dashboard.stripe.com/customers/{stripe_subscription.customer_id}|{stripe_subscription.plan.product.name}> (${str(total_spent)})",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f":date: *Customer since:* {start_date} (~{timesince})",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f":books: *Projects:* {organization.projects.count()}",
                        },
                        {"type": "mrkdwn", "text": f":link: *Domains:* {domains}"},
                        {
                            "type": "mrkdwn",
                            "text": f":closed_lock_with_key: *Authentication:* {sso_integration}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f":busts_in_silhouette: *Teams:* {organization.teams.count()}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "We should contact this customer and see if we can get some feedback from them.",
                        }
                    ],
                },
            ]
        }
        try:
            response = requests.post(
                settings.SLACK_WEBHOOK_SALES_CHANNEL,
                json=slack_message,
                timeout=3,
            )
            if not response.ok:
                log.error("There was an issue when sending a message to Slack webhook")

        except requests.Timeout:
            log.warning("Timeout sending a message to Slack webhook")


@handler("customer.updated")
def customer_updated_event(event):
    """Update the organization with the new information from the stripe customer."""
    stripe_customer = event.data["object"]
    log.bind(stripe_customer_id=stripe_customer["id"])
    organization = Organization.objects.filter(stripe_id=stripe_customer["id"]).first()
    if not organization:
        log.error("Customer isn't attached to an organization.")

    new_email = stripe_customer["email"]
    if organization.email != new_email:
        organization.email = new_email
        organization.save()
        log.info(
            "Organization billing email updated.",
            organization_slug=organization.slug,
            email=new_email,
        )
