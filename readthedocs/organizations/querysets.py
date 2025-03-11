"""Organizations querysets."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from djstripe.enums import InvoiceStatus
from djstripe.enums import SubscriptionStatus

from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.subscriptions.constants import DISABLE_AFTER_DAYS


class BaseOrganizationQuerySet(NoReprQuerySet, models.QuerySet):
    """Organizations queryset."""

    def for_user(self, user):
        # Never list all for membership
        return self.filter(
            Q(owners__in=[user]) | Q(teams__members__in=[user]),
        ).distinct()

    def for_admin_user(self, user):
        return self.filter(owners__in=[user]).distinct()

    def api(self, user):
        return self.for_user(user)

    def created_days_ago(self, days, field="pub_date"):
        """
        Filter organizations by creation date.

        :param days: Days ago that organization was created
        :param field: Field name to use in comparison, default: pub_date
        """
        when = timezone.now() - timedelta(days=days)
        query_filter = {}
        query_filter[field + "__year"] = when.year
        query_filter[field + "__month"] = when.month
        query_filter[field + "__day"] = when.day
        return self.filter(**query_filter)

    def subscription_trial_plan_ended(self):
        """
        Organizations with subscriptions to Trial Plan ended.

        Trial Plan in Stripe has a 30-day trial set up. After that period ends,
        the subscription is canceled.
        """
        return self.filter(
            stripe_subscription__status=SubscriptionStatus.canceled,
            stripe_subscription__items__price__id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE,
        )

    def subscription_ended(self, days, exact=False):
        """
        Filter organizations which their subscription has ended.

        This will return organizations which their subscription has been canceled,
        or hasn't been paid for ``days``.

        :param days: Days after the subscription has ended
        :param exact: Make the ``days`` date to match exactly that day after the
            subscription has ended (useful to send emails only once)
        """
        date_today = timezone.now().date()
        end_date = date_today - timedelta(days=days)

        if exact:
            # We use ``__date`` here since the field is a DateTimeField
            subscription_ended = self.filter(
                Q(
                    stripe_subscription__status=SubscriptionStatus.canceled,
                    stripe_subscription__ended_at__date=end_date,
                )
                | Q(
                    stripe_subscription__status__in=[
                        SubscriptionStatus.past_due,
                        SubscriptionStatus.incomplete,
                        SubscriptionStatus.unpaid,
                    ],
                    stripe_subscription__latest_invoice__due_date__date=end_date,
                    stripe_subscription__latest_invoice__status=InvoiceStatus.open,
                )
            )
        else:
            subscription_ended = self.filter(
                Q(
                    stripe_subscription__status=SubscriptionStatus.canceled,
                    stripe_subscription__ended_at__lt=end_date,
                )
                | Q(
                    stripe_subscription__status__in=[
                        SubscriptionStatus.past_due,
                        SubscriptionStatus.incomplete,
                        SubscriptionStatus.unpaid,
                    ],
                    stripe_subscription__latest_invoice__due_date__date__lt=end_date,
                    stripe_subscription__latest_invoice__status=InvoiceStatus.open,
                )
            )

        return subscription_ended.distinct()

    def disable_soon(self, days, exact=False):
        """
        Filter organizations that will eventually be marked as disabled.

        These are organizations which their subscription has ended,
        excluding organizations that can't be disabled, or are already disabled.

        :param days: Days after the subscription has ended
        :param exact: Make the ``days`` date to match exactly that day after the
            subscription has ended (useful to send emails only once)
        """
        return (
            self.subscription_ended(days=days, exact=exact)
            # Exclude organizations that can't be disabled.
            .exclude(never_disable=True)
            # Exclude organizations that are already disabled
            .exclude(disabled=True)
        )

    def clean_artifacts(self):
        """
        Filter organizations which their artifacts can be cleaned up.

        These organizations are at least 3*DISABLE_AFTER_DAYS (~3 months) that
        are disabled and their artifacts weren't cleaned already. We should be
        safe to cleanup all their artifacts at this point.
        """
        return self.subscription_ended(days=3 * DISABLE_AFTER_DAYS, exact=False).filter(
            disabled=True,
            artifacts_cleaned=False,
        )

    def single_owner(self, user):
        """Returns organizations where `user` is the only owner."""
        return self.annotate(count_owners=Count("owners")).filter(
            owners=user,
            count_owners=1,
        )


class OrganizationQuerySet(SettingsOverrideObject):
    _default_class = BaseOrganizationQuerySet
