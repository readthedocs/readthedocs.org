"""
Querysets for djstripe models.

Since djstripe is a third-party app,
these are injected at runtime at readthedocs/subscriptions/apps.py.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone
from djstripe.enums import SubscriptionStatus

from readthedocs.core.querysets import NoReprQuerySet


class StripeSubscriptionQueryset(NoReprQuerySet, models.QuerySet):
    """Manager for the djstripe Subscription model."""

    def trial_ending(self, days=7):
        """Get all subscriptions where their trial will end in the next `days`."""
        now = timezone.now()
        ending = now + timedelta(days=days)
        return self.filter(
            status=SubscriptionStatus.trialing,
            trial_end__gt=now,
            trial_end__lt=ending,
        ).distinct()

    def created_days_ago(self, days):
        """Get all subscriptions that were created exactly `days` ago."""
        when = timezone.now() - timedelta(days=days)
        return self.filter(created__date=when)
