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

log = structlog.get_logger(__name__)


def _update_subscription_from_stripe(rtd_subscription, stripe_subscription_id):
    """Update the RTD subscription object given the new stripe subscription object."""
    log.bind(stripe_subscription=stripe_subscription_id)
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
        previous_stripe_subscription=previous_subscription_id,
        subscription_status=stripe_subscription.status,
    )

    # Cancel the trial subscription if its trial has ended.
    trial_ended = (
        stripe_subscription.trial_end and stripe_subscription.trial_end < timezone.now()
    )
    is_trial_subscription = stripe_subscription.items.filter(
        price__id=settings.RTD_ORG_DEFAULT_STRIPE_PRICE
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


@webhooks.handler("customer.subscription.updated", "customer.subscription.deleted")
def update_subscription(event):
    """Update the RTD subscription object given the new stripe subscription."""
    stripe_subscription_id = event.data["object"]["id"]
    rtd_subscription = Subscription.objects.filter(
        stripe_id=stripe_subscription_id
    ).first()
    if not rtd_subscription:
        log.info(
            "Stripe subscription isn't attached to a RTD object.",
            stripe_subscription=stripe_subscription_id,
        )
        return

    _update_subscription_from_stripe(
        rtd_subscription=rtd_subscription,
        stripe_subscription_id=stripe_subscription_id,
    )


@webhooks.handler("checkout.session.completed")
def checkout_completed(event):
    """
    Handle the creation of a new subscription via stripe checkout.

    Stripe checkout will create a new subscription,
    so we need to replace the older one with the new one.
    """
    customer_id = event.data["object"]["customer"]
    organization = Organization.objects.filter(stripe_customer__id=customer_id).first()
    if not organization:
        log.info(
            "Customer isn't attached to an organization.",
            customer_id=customer_id,
        )
        return

    stripe_subscription_id = event.data["object"]["subscription"]
    _update_subscription_from_stripe(
        rtd_subscription=organization.subscription,
        stripe_subscription_id=stripe_subscription_id,
    )


@webhooks.handler("customer.updated")
def customer_updated_event(event):
    """Update the organization with the new information from the stripe customer."""
    stripe_customer = event.data["object"]
    log.bind(customer=stripe_customer["id"])
    organization = Organization.objects.filter(stripe_id=stripe_customer["id"]).first()
    if not organization:
        log.info("Customer isn't attached to an organization.")

    new_email = stripe_customer["email"]
    if organization.email != new_email:
        organization.email = new_email
        organization.save()
        log.info(
            "Organization billing email updated.",
            organization_slug=organization.slug,
            email=new_email,
        )
