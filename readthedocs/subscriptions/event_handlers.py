"""
Dj-stripe webhook handlers.

https://docs.dj-stripe.dev/en/master/usage/webhooks/.
"""
import structlog
from django.conf import settings
from django.utils import timezone
from djstripe import models as djstripe
from djstripe import webhooks
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.payments.utils import cancel_subscription as cancel_stripe_subscription
from readthedocs.subscriptions.models import Subscription
from readthedocs.subscriptions.notifications import (
    SubscriptionEndedNotification,
    SubscriptionRequiredNotification,
)

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


def _update_subscription_from_stripe(rtd_subscription, stripe_subscription_id):
    """Update the RTD subscription object given the new stripe subscription object."""
    log.bind(stripe_subscription_id=stripe_subscription_id)
    stripe_subscription = djstripe.Subscription.objects.filter(
        id=stripe_subscription_id
    ).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return

    previous_subscription_id = rtd_subscription.stripe_id
    Subscription.objects.update_from_stripe(
        rtd_subscription=rtd_subscription,
        stripe_subscription=stripe_subscription,
    )
    log.info(
        "Subscription updated.",
        previous_stripe_subscription_id=previous_subscription_id,
        stripe_subscription_status=stripe_subscription.status,
    )

    # Cancel the trial subscription if its trial has ended.
    trial_ended = (
        stripe_subscription.trial_end and stripe_subscription.trial_end < timezone.now()
    )
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


@handler("customer.subscription.updated", "customer.subscription.deleted")
def update_subscription(event):
    """Update the RTD subscription object with the updates from the Stripe subscription."""
    stripe_subscription_id = event.data["object"]["id"]
    rtd_subscription = Subscription.objects.filter(
        stripe_id=stripe_subscription_id
    ).first()
    if not rtd_subscription:
        log.info(
            "Stripe subscription isn't attached to a RTD object.",
            stripe_subscription_id=stripe_subscription_id,
        )
        return

    _update_subscription_from_stripe(
        rtd_subscription=rtd_subscription,
        stripe_subscription_id=stripe_subscription_id,
    )


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
    stripe_subscription = djstripe.Subscription.objects.filter(
        id=stripe_subscription_id
    ).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return

    organization = stripe_subscription.customer.rtd_organization
    if not organization:
        log.error("Subscription isn't attached to an organization")
        return

    log.bind(organization_slug=organization.slug)
    is_trial_subscription = stripe_subscription.items.filter(
        price__id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE
    ).exists()
    notification_class = (
        SubscriptionRequiredNotification
        if is_trial_subscription
        else SubscriptionEndedNotification
    )
    for owner in organization.owners.all():
        notification = notification_class(
            context_object=organization,
            user=owner,
        )
        notification.send()
        log.info("Notification sent.", recipient=owner)


@handler("checkout.session.completed")
def checkout_completed(event):
    """
    Handle the creation of a new subscription via Stripe Checkout.

    Stripe checkout will create a new subscription,
    so we need to replace the older one with the new one.
    """
    customer_id = event.data["object"]["customer"]
    organization = Organization.objects.filter(stripe_customer__id=customer_id).first()
    if not organization:
        log.error(
            "Customer isn't attached to an organization.",
            stripe_customer_id=customer_id,
        )
        return

    stripe_subscription_id = event.data["object"]["subscription"]
    stripe_subscription = djstripe.Subscription.objects.filter(
        id=stripe_subscription_id
    ).first()
    if not stripe_subscription:
        log.info("Stripe subscription not found.")
        return
    organization.stripe_subscription = stripe_subscription
    organization.save()

    _update_subscription_from_stripe(
        rtd_subscription=organization.subscription,
        stripe_subscription_id=stripe_subscription_id,
    )


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
