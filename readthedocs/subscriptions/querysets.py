"""
Querysets for djstripe models.

Since djstripe is a third-party app,
these are injected at runtime at readthedocs/subscriptions/apps.py.
"""
from datetime import timedelta

from django.db import models
from django.utils import timezone
from djstripe.enums import SubscriptionStatus


class StripeSubscriptionQueryset(models.QuerySet):
    def trial_ending(self, days=7):
        now = timezone.now()
        ending = now + timedelta(days=days)
        return self.filter(
            status=SubscriptionStatus.trialing,
            trial_end__gt=now,
            trial_end__lt=ending,
        ).distinct()

    def created_days_ago(self, days):
        when = timezone.now() - timedelta(days=days)
        return self.filter(created__date=when)
