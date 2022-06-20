"""
Payment utility functions.

These are mostly one-off functions. Define the bulk of Stripe operations on
:py:class:`readthedocs.payments.forms.StripeResourceMixin`.
"""

import stripe
import structlog
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET
stripe.api_version = settings.STRIPE_VERSION
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
            'Customer not deleted. Customer not found on Stripe.',
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
