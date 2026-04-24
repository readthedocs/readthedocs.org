"""Utilities to interact with subscriptions and stripe."""

import structlog
from django.conf import settings
from djstripe import models as djstripe

from readthedocs.payments.utils import get_stripe_api_key
from readthedocs.payments.utils import get_stripe_client


log = structlog.get_logger(__name__)


def create_stripe_customer(organization):
    """Create a stripe customer for organization."""
    stripe_client = get_stripe_client()
    stripe_data = stripe_client.customers.create(
        params={
            "email": organization.email,
            "name": organization.name,
            "description": organization.name,
            "metadata": organization.get_stripe_metadata(),
        },
    )

    # NOTE: we need to pass the `api_key` here due to a bug in dj-stripe
    # See the related issues
    # * https://github.com/dj-stripe/dj-stripe/issues/2055
    # * https://github.com/dj-stripe/dj-stripe/issues/2037
    stripe_key = get_stripe_api_key()
    stripe_customer = djstripe.Customer.sync_from_stripe_data(stripe_data, api_key=stripe_key)

    organization.stripe_customer = stripe_customer
    organization.save()
    return stripe_customer


def get_or_create_stripe_customer(organization):
    """
    Retrieve the stripe customer or create a new one.

    If `organization.stripe_customer` is `None`, a new customer is created.
    """
    structlog.contextvars.bind_contextvars(organization_slug=organization.slug)
    stripe_customer = organization.stripe_customer
    if stripe_customer:
        return stripe_customer
    log.info("No stripe customer found, creating one.")
    return create_stripe_customer(organization)


def get_or_create_stripe_subscription(organization):
    """
    Get the stripe subscription attached to the organization or create one.

    The subscription will be created with the default price and a trial period.
    """
    stripe_customer = get_or_create_stripe_customer(organization)
    stripe_subscription = organization.get_stripe_subscription()
    if not stripe_subscription:
        stripe_key = get_stripe_api_key()
        stripe_subscription = stripe_customer.subscribe(
            items=[{"price": settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE}],
            trial_period_days=settings.RTD_ORG_TRIAL_PERIOD_DAYS,
            api_key=stripe_key,
        )
    if organization.stripe_subscription != stripe_subscription:
        organization.stripe_subscription = stripe_subscription
        organization.save()
    return stripe_subscription
