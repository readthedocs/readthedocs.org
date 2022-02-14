"""Utilities to interact with subscriptions and stripe."""

import structlog

import stripe
from stripe.error import InvalidRequestError

log = structlog.get_logger(__name__)


def create_stripe_customer(organization):
    """Create a stripe customer for organization."""
    stripe_customer = stripe.Customer.create(
        email=organization.email,
        description=organization.name,
    )
    if organization.stripe_id:
        log.warning(
            'Overriding existing stripe customer. ',
            organization_slug=organization.slug,
            previous_stripe_customer=organization.stripe_id,
            stripe_customer=stripe_customer.id,
        )
    organization.stripe_id = stripe_customer.id
    organization.save()
    return stripe_customer


def get_or_create_stripe_customer(organization):
    """
    Retrieve the stripe customer from `organization.stripe_id` or create a new one.

    If `organization.stripe_id` is `None` or if the existing customer
    doesn't exist in stripe, a new customer is created.
    """
    log.bind(
        organization_slug=organization.slug,
        stripe_customer=organization.stripe_id,
    )
    if not organization.stripe_id:
        log.info('No stripe customer found, creating one.')
        return create_stripe_customer(organization)

    try:
        log.debug('Retrieving existing stripe customer.')
        stripe_customer = stripe.Customer.retrieve(organization.stripe_id)
        return stripe_customer
    except InvalidRequestError as exc:
        if exc.code == 'resource_missing':
            log.info('Invalid stripe customer, creating new one.')
            return create_stripe_customer(organization)
        log.exception('Error while retrieving stripe customer.')
        raise
