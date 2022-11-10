"""Organizations querysets."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.subscriptions.constants import DISABLE_AFTER_DAYS


class BaseOrganizationQuerySet(models.QuerySet):

    """Organizations queryset."""

    def for_user(self, user):
        # Never list all for membership
        return self.filter(
            Q(owners__in=[user]) | Q(teams__members__in=[user]),
        ).distinct()

    def for_admin_user(self, user):
        return self.filter(owners__in=[user],).distinct()

    def created_days_ago(self, days, field='pub_date'):
        """
        Filter organizations by creation date.

        :param days: Days ago that organization was created
        :param field: Field name to use in comparison, default: pub_date
        """
        when = timezone.now() - timedelta(days=days)
        query_filter = {}
        query_filter[field + '__year'] = when.year
        query_filter[field + '__month'] = when.month
        query_filter[field + '__day'] = when.day
        return self.filter(**query_filter)

    # TODO: once we are settled into the Trial Plan, merge this method with the
    # following one (``subscription_trial_ended``).
    def subscription_trial_plan_ended(self):
        """
        Organizations with subscriptions to Trial Plan ended.

        Trial Plan in Stripe has a 30-day trial set up. After that period ends,
        the subscription goes to ``active`` and we know that the trial ended.

        It also checks that ``end_date`` or ``trial_end_date`` are in the past.
        """
        date_now = timezone.now()
        return self.filter(
            ~Q(subscription__status="trialing"),
            Q(
                subscription__plan__stripe_id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE
            ),
            Q(subscription__end_date__lt=date_now)
            | Q(subscription__trial_end_date__lt=date_now),
        )

    def subscription_trial_ended(self):
        """
        Organizations with subscriptions in trial ended state.

        Filter for organization subscription past the trial date, or
        organizations older than 30 days old
        """
        date_now = timezone.now()
        return self.filter(
            Q(
                (
                    Q(
                        subscription__status='trialing',
                    ) | Q(
                        subscription__status__exact='',
                    )
                ),
                subscription__trial_end_date__lt=date_now,
            ) | Q(
                subscription__isnull=True,
                pub_date__lt=date_now - timedelta(days=30),
            ),
        )

    def subscription_ended(self):
        """
        Organization with paid subscriptions ended.

        Filter for organization with paid subscriptions that have
        ended (canceled, past_due or unpaid) and they didn't renew them yet.

        https://stripe.com/docs/api#subscription_object-status
        """
        return self.filter(
            subscription__status__in=['canceled', 'past_due', 'unpaid'],
        )

    def disable_soon(self, days, exact=False):
        """
        Filter organizations that will eventually be marked as disabled.

        This will return organizations that the paid/trial subscription has
        ended ``days`` ago.

        :param days: Days after the subscription has ended
        :param exact: Make the ``days`` date to match exactly that day after the
            subscription has ended (useful to send emails only once)
        """
        date_today = timezone.now().date()
        end_date = date_today - timedelta(days=days)

        if exact:
            # We use ``__date`` here since the field is a DateTimeField
            trial_filter = {'subscription__trial_end_date__date': end_date}
            paid_filter = {'subscription__end_date__date': end_date}
        else:
            trial_filter = {'subscription__trial_end_date__lt': end_date}
            paid_filter = {'subscription__end_date__lt': end_date}

        trial_ended = self.subscription_trial_ended().filter(**trial_filter)
        paid_ended = self.subscription_ended().filter(**paid_filter)

        # Exclude organizations with custom plans (locked=True)
        orgs = (trial_ended | paid_ended).exclude(subscription__locked=True)

        # Exclude organizations that are already disabled
        orgs = orgs.exclude(disabled=True)

        return orgs.distinct()

    def clean_artifacts(self):
        """
        Filter organizations which their artifacts can be cleaned up.

        These organizations are at least 3*DISABLE_AFTER_DAYS (~3 months) that
        are disabled and their artifacts weren't cleaned already. We should be
        safe to cleanup all their artifacts at this point.
        """
        end_date = timezone.now().date() - timedelta(days=3 * DISABLE_AFTER_DAYS)
        orgs = self.filter(
            disabled=True,
            subscription__end_date__lt=end_date,
            artifacts_cleaned=False,
        )
        return orgs.distinct()

    def single_owner(self, user):
        """Returns organizations where `user` is the only owner."""
        return self.annotate(count_owners=Count("owners")).filter(
            owners=user,
            count_owners=1,
        )


class OrganizationQuerySet(SettingsOverrideObject):

    _default_class = BaseOrganizationQuerySet
