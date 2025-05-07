"""
Payment utility functions.

These are mostly one-off functions. Define the bulk of Stripe operations on
:py:class:`readthedocs.payments.forms.StripeResourceMixin`.
"""

import stripe
import structlog
from djstripe.models import APIKey


stripe.api_key = APIKey.objects.filter(type="secret").first().secret
log = structlog.get_logger(__name__)


def delete_customer(customer_id):
    """Delete customer from Stripe, cancelling subscriptions."""
    try:
        log.info(
            "Deleting stripe customer.",
            stripe_customer=customer_id,
        )
        customer = stripe.Customer.retrieve(customer_id)
        return customer.delete()
    except stripe.error.InvalidRequestError:
        log.exception(
            "Customer not deleted. Customer not found on Stripe.",
            stripe_customer=customer_id,
        )


def cancel_subscription(subscription_id):
    """Cancel Stripe subscription, if it exists."""
    try:
        log.info(
            "Canceling stripe subscription.",
            stripe_subscription=subscription_id,
        )
        return stripe.Subscription.delete(subscription_id)
    except stripe.error.StripeError:
        log.exception(
            "Subscription not cancelled. Subscription not found on Stripe. ",
            stripe_subscription=subscription_id,
        )
