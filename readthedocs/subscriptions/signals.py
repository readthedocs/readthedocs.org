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
        if subscription.stripe_id and subscription.organization.stripe_id:
            log.info('Removing organization Stripe subscription.')
            cancel_subscription(subscription.organization.stripe_id, subscription.stripe_id)
        else:
            log.exception("Can't remove Stripe subscription. Organization didn't have ID.")

    except Organization.DoesNotExist:
        log.exception(
            'Subscription has no organization. No subscription to cancel.',
            subscription_id=subscription.pk,
        )


# pylint: disable=unused-argument
@receiver(post_save, sender=Organization)
def update_billing_information(sender, instance, created, **kwargs):
    """Update billing email information."""
    if created:
        return

    organization = instance
    log.bind(organization_slug=organization.slug)
    # pylint: disable=broad-except
    try:
        s_customer = stripe.Customer.retrieve(organization.stripe_id)
        if s_customer.email != organization.email:
            s_customer.email = organization.email
            s_customer.save()
    except stripe.error.StripeError:
        log.exception('Unable to update the Organization billing email on Stripe.')
    except Exception:
        log.exception('Unknown error when updating Organization billing email on Stripe.')


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
