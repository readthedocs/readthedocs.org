"""
Payment utility functions.

These are mostly one-off functions. Define the bulk of Stripe operations on
:py:class:`readthedocs.payments.forms.StripeResourceMixin`.
"""

import stripe
import structlog
from django.conf import settings
from djstripe.models import Account


log = structlog.get_logger(__name__)


def get_stripe_api_key():
    """Return Stripe API key defined in the dj-stripe database."""
    return Account.objects.first().get_default_api_key(livemode=settings.STRIPE_LIVE_MODE)


def get_stripe_client():
    """Return Stripe API client using the API key defined in the dj-stripe database."""
    api_key = get_stripe_api_key()
    return stripe.StripeClient(api_key)


def delete_customer(customer_id):
    """Delete customer from Stripe, cancelling subscriptions."""
    stripe_client = get_stripe_client()
    try:
        log.info(
            "Deleting stripe customer.",
            stripe_customer=customer_id,
        )
        customer = stripe_client.customers.retrieve(customer_id)
        return customer.delete()
    except stripe.error.InvalidRequestError:
        log.exception(
            "Customer not deleted. Customer not found on Stripe.",
            stripe_customer=customer_id,
        )


def cancel_subscription(subscription_id):
    """Cancel Stripe subscription, if it exists."""
    stripe_client = get_stripe_client()
    try:
        log.info(
            "Canceling stripe subscription.",
            stripe_subscription=subscription_id,
        )
        return stripe_client.subscriptions.cancel(subscription_id)
    except stripe.error.StripeError:
        log.exception(
            "Subscription not cancelled. Subscription not found on Stripe. ",
            stripe_subscription=subscription_id,
        )
