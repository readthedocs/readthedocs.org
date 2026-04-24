"""Subscriptions signals."""

import stripe
import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.organizations.models import Organization
from readthedocs.payments.utils import get_stripe_client


log = structlog.get_logger(__name__)


# pylint: disable=unused-argument
@receiver(post_save, sender=Organization)
def update_stripe_customer(sender, instance, created, **kwargs):
    """Update email and metadata attached to the stripe customer."""
    if created:
        return

    organization = instance
    structlog.contextvars.bind_contextvars(organization_slug=organization.slug)

    stripe_customer = organization.stripe_customer
    if not stripe_customer:
        log.warning("Organization doesn't have a stripe customer attached.")
        return

    fields_to_update = {}
    if organization.email != stripe_customer.email:
        fields_to_update["email"] = organization.email

    if organization.name != stripe_customer.description:
        fields_to_update["description"] = organization.name

    if organization.name != stripe_customer.name:
        fields_to_update["name"] = organization.name

    org_metadata = organization.get_stripe_metadata()
    current_metadata = stripe_customer.metadata or {}
    for key, value in org_metadata.items():
        if current_metadata.get(key) != value:
            current_metadata.update(org_metadata)
            fields_to_update["metadata"] = current_metadata
            break

    if fields_to_update:
        # pylint: disable=broad-except
        stripe_client = get_stripe_client()
        try:
            stripe_client.customers.update(
                stripe_customer.id,
                params=fields_to_update,
            )
        except stripe.error.StripeError:
            log.exception("Unable to update stripe customer.")
        except Exception:
            log.exception("Unknown error when updating stripe customer.")
