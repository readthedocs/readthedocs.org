# -*- coding: utf-8 -*-

"""Gold model signals."""

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from readthedocs.payments import utils

from .models import GoldUser


@receiver(pre_delete, sender=GoldUser)
def delete_customer(sender, instance, **__):
    """On Gold subscription deletion, remove the customer from Stripe."""
    if sender == GoldUser and instance.stripe_id is not None:
        utils.delete_customer(instance.stripe_id)
