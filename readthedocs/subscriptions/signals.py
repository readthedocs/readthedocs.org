"""Subscriptions signals."""

import stripe
import structlog
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from readthedocs.organizations.models import Organization
from readthedocs.payments.utils import cancel_subscription
from readthedocs.subscriptions.models import Subscription

log = structlog.get_logger(__name__)


# pylint: disable=unused-argument
@receiver(pre_delete, sender=Subscription)
def remove_stripe_subscription(sender, instance, using, **kwargs):
    """Remove Stripe subscription on Subscription delete."""
    subscription = instance
    try:
        log.bind(organization_slug=subscription.organization.slug)
        if subscription.stripe_id:
            log.info('Removing organization Stripe subscription.')
            cancel_subscription(subscription.stripe_id)
        else:
            log.exception("Can't remove Stripe subscription. Organization didn't have ID.")

    except Organization.DoesNotExist:
        log.exception(
            'Subscription has no organization. No subscription to cancel.',
            subscription_id=subscription.pk,
        )


# pylint: disable=unused-argument
@receiver(post_save, sender=Organization)
def update_stripe_customer(sender, instance, created, **kwargs):
    """Update email and metadata attached to the stripe customer."""
    if created:
        return

    organization = instance
    log.bind(organization_slug=organization.slug)

    stripe_customer = organization.stripe_customer
    if not stripe_customer:
        log.warning("Organization doesn't have a stripe customer attached.")
        return

    fields_to_update = {}
    if organization.email != stripe_customer.email:
        fields_to_update["email"] = organization.email

    org_metadata = organization.get_stripe_metadata()
    current_metadata = stripe_customer.metadata or {}
    for key, value in org_metadata.items():
        if current_metadata.get(key) != value:
            current_metadata.update(org_metadata)
            fields_to_update["metadata"] = current_metadata
            break

    if fields_to_update:
        # pylint: disable=broad-except
        try:
            stripe.Customer.modify(
                stripe_customer.id,
                **fields_to_update,
            )
        except stripe.error.StripeError:
            log.exception("Unable to update stripe customer.")
        except Exception:
            log.exception("Unknown error when updating stripe customer.")


# pylint: disable=unused-argument
@receiver(pre_delete, sender=Organization)
def remove_subscription(sender, instance, using, **kwargs):
    """
    Deletes the subscription object and cancels it from Stripe.

    This is used as complement to ``remove_organization_completely``.
    """
    organization = instance
    try:
        subscription = organization.subscription
        subscription.delete()
    except Subscription.DoesNotExist:
        log.error(
            "Organization doesn't have a subscription to cancel.",
            organization_slug=organization.slug,
        )
