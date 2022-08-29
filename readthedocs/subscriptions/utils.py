"""Utilities to interact with subscriptions and stripe."""

import stripe
import structlog
from djstripe import models as djstripe
from stripe.error import InvalidRequestError

log = structlog.get_logger(__name__)


def create_stripe_customer(organization):
    """Create a stripe customer for organization."""
    stripe_data = stripe.Customer.create(
        email=organization.email,
        description=organization.name,
        metadata=organization.get_stripe_metadata(),
    )
    stripe_customer = djstripe.Customer.sync_from_stripe_data(stripe_data)
    if organization.stripe_id:
        log.warning(
            "Overriding existing stripe customer.",
            organization_slug=organization.slug,
            previous_stripe_customer=organization.stripe_id,
            stripe_customer=stripe_customer.id,
        )
    organization.stripe_customer = stripe_customer
    organization.save()
    return stripe_customer


def get_or_create_stripe_customer(organization):
    """
    Retrieve the stripe customer or create a new one.

    If `organization.stripe_customer` is `None`, a new customer is created.
    Not all models are migrated to use djstripe yet,
    so we retrieve the customer from the stripe_id attribute if the model has one.
    """
    log.bind(
        organization_slug=organization.slug,
        stripe_customer=organization.stripe_id,
    )
    stripe_customer = organization.stripe_customer
    if not stripe_customer:
        stripe_customer = None
        if organization.stripe_id:
            try:
                # TODO: Don't fully trust on djstripe yet,
                # the customer may not be in our DB yet.
                # pylint: disable=protected-access
                stripe_customer = djstripe.Customer._get_or_retrieve(
                    organization.stripe_id
                )
            except InvalidRequestError as exc:
                if exc.code == "resource_missing":
                    log.info("Invalid stripe customer, creating new one.")

        if stripe_customer:
            metadata = stripe_customer.metadata or {}
            metadata.update(organization.get_stripe_metadata())
            stripe.Customer.modify(
                stripe_customer.id,
                metadata=metadata,
            )
            organization.stripe_customer = stripe_customer
            organization.save()
        else:
            log.info("No stripe customer found, creating one.")
            return create_stripe_customer(organization)
    return stripe_customer
