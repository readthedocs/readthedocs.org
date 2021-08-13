# -*- coding: utf-8 -*-

"""
Payment utility functions.

These are mostly one-off functions. Define the bulk of Stripe operations on
:py:class:`readthedocs.payments.forms.StripeResourceMixin`.
"""

import logging

import stripe

from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET
log = logging.getLogger(__name__)


def delete_customer(customer_id):
    """Delete customer from Stripe, cancelling subscriptions."""
    try:
        customer = stripe.Customer.retrieve(customer_id)
        return customer.delete()
    except stripe.error.InvalidRequestError:
        log.exception(
            'Customer not deleted. Customer not found on Stripe. customer=%s',
            customer_id,
        )


def cancel_subscription(customer_id, subscription_id):
    """Cancel Stripe subscription, if it exists."""
    try:
        customer = stripe.Customer.retrieve(customer_id)
        if hasattr(customer, 'subscriptions'):
            subscription = customer.subscriptions.retrieve(subscription_id)
            return subscription.delete()
    except stripe.error.StripeError:
        log.exception(
            'Subscription not cancelled. Customer/Subscription not found on Stripe. '
            'customer=%s subscription=%s',
            customer_id,
            subscription_id,
        )
