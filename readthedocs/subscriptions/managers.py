"""Subscriptions managers."""

from datetime import datetime

import stripe
import structlog
from django.conf import settings
from django.db import models
from django.utils import timezone

from readthedocs.core.history import set_change_reason
from readthedocs.subscriptions.utils import get_or_create_stripe_customer

log = structlog.get_logger(__name__)


class SubscriptionManager(models.Manager):

    """Model manager for Subscriptions."""

    def get_or_create_default_subscription(self, organization):
        """
        Get or create a trialing subscription for `organization`.

        If the organization doesn't have a subscription attached,
        the following steps are executed.

        - If the organization doesn't have a stripe customer, one is created.
        - A new stripe subscription is created using the default plan.
        - A new subscription object is created in our database
          with the information from the stripe subscription.
        """
        if hasattr(organization, 'subscription'):
            return organization.subscription

        from readthedocs.subscriptions.models import Plan
        plan = Plan.objects.filter(slug=settings.ORG_DEFAULT_SUBSCRIPTION_PLAN_SLUG).first()
        # This should happen only on development.
        if not plan:
            log.warning(
                'No default plan found, not creating a subscription.',
                organization_slug=organization.slug,
            )
            return None

        stripe_customer = get_or_create_stripe_customer(organization)
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer.id,
            items=[{"price": plan.stripe_id}],
            trial_period_days=plan.trial,
        )
        # Stripe renamed ``start`` to ``start_date``,
        # our API calls will return the new object,
        # but webhooks will still return the old object
        # till we change the default version.
        # TODO: use stripe_subscription.start_date after the webhook version has been updated.
        start_date = getattr(
            stripe_subscription, "start", getattr(stripe_subscription, "start_date")
        )
        return self.create(
            plan=plan,
            organization=organization,
            stripe_id=stripe_subscription.id,
            status=stripe_subscription.status,
            start_date=timezone.make_aware(
                datetime.fromtimestamp(int(start_date)),
            ),
            end_date=timezone.make_aware(
                datetime.fromtimestamp(int(stripe_subscription.current_period_end)),
            ),
            trial_end_date=timezone.make_aware(
                datetime.fromtimestamp(int(stripe_subscription.trial_end)),
            ),
        )

    def update_from_stripe(self, *, rtd_subscription, stripe_subscription):
        """
        Update the RTD subscription object with the information of the stripe subscription.

        :param subscription: Subscription object to update.
        :param stripe_subscription: Stripe subscription object from API
        :type stripe_subscription: stripe.Subscription
        """
        # Documentation doesn't say what will be this value once the
        # subscription is ``canceled``. I'm assuming that ``current_period_end``
        # will have the same value than ``ended_at``
        # https://stripe.com/docs/api/subscriptions/object?lang=python#subscription_object-current_period_end
        start_date = getattr(stripe_subscription, 'current_period_start', None)
        end_date = getattr(stripe_subscription, 'current_period_end', None)
        log.bind(stripe_subscription=stripe_subscription.id)

        try:
            start_date = timezone.make_aware(
                datetime.fromtimestamp(start_date),
            )
            end_date = timezone.make_aware(
                datetime.fromtimestamp(end_date),
            )
        except TypeError:
            log.error(
                'Stripe subscription invalid date.',
                start_date=start_date,
                end_date=end_date,
            )
            start_date = None
            end_date = None
            trial_end_date = None

        rtd_subscription.status = stripe_subscription.status

        # This should only happen if an existing user creates a new subscription,
        # after their previous subscription was cancelled.
        if stripe_subscription.id != rtd_subscription.stripe_id:
            log.info(
                'Replacing stripe subscription.',
                old_stripe_subscription=rtd_subscription.stripe_id,
                new_stripe_subscription=stripe_subscription.id,
            )
            rtd_subscription.stripe_id = stripe_subscription.id

        # Update trial end date if it's present
        trial_end_date = getattr(stripe_subscription, 'trial_end', None)
        if trial_end_date:
            try:
                trial_end_date = timezone.make_aware(
                    datetime.fromtimestamp(trial_end_date),
                )
                rtd_subscription.trial_end_date = trial_end_date
            except TypeError:
                log.error(
                    'Stripe subscription trial end date invalid. ',
                    trial_end_date=trial_end_date,
                )

        # Update the plan in case it was changed from the Portal.
        # This mostly just updates the UI now that we're using the Stripe Portal.
        # A miss here just won't update the UI, but this shouldn't happen for most users.
        # NOTE: Previously we were using stripe_subscription.plan,
        # but that attribute is deprecated, and it's null if the subscription has more than
        # one item, we have a couple of subscriptions that have more than
        # one item, so we use the first that is found in our DB.
        for stripe_item in stripe_subscription["items"].data:
            plan = self._get_plan(stripe_item.price)
            if plan:
                rtd_subscription.plan = plan
                break
        else:
            log.error("Plan not found, skipping plan update.")

        if stripe_subscription.status == 'canceled':
            # Remove ``stripe_id`` when canceled so the customer can
            # re-subscribe using our form.
            rtd_subscription.stripe_id = None

        elif stripe_subscription.status == 'active' and end_date:
            # Save latest active date (end_date) to notify owners about their subscription
            # is ending and disable this organization after N days of unpaid. We check for
            # ``active`` here because Stripe will continue sending updates for the
            # subscription, with a new ``end_date``, even after the subscription enters
            # an unpaid state.
            rtd_subscription.end_date = end_date

        elif stripe_subscription.status == 'past_due' and start_date:
            # When Stripe marks the subscription as ``past_due``,
            # it means the usage of RTD service for the current period/month was not paid at all.
            # At this point, we need to update our ``end_date`` to the last period the customer paid
            # (which is the start date of the current ``past_due`` period --it could be the end date
            # of the trial or the end date of the last paid period).
            rtd_subscription.end_date = start_date

        klass = self.__class__.__name__
        change_reason = f'origin=stripe-subscription class={klass}'

        # Ensure that the organization is in the correct state.
        # We want to always ensure the organization is never disabled
        # if the subscription is valid.
        organization = rtd_subscription.organization
        if stripe_subscription.status == 'active' and organization.disabled:
            log.warning(
                'Re-enabling organization with valid subscription.',
                organization_slug=organization.slug,
                stripe_subscription=rtd_subscription.id,
            )
            organization.disabled = False
            set_change_reason(organization, change_reason)
            organization.save()

        set_change_reason(rtd_subscription, change_reason)
        rtd_subscription.save()
        return rtd_subscription

    # pylint: disable=no-self-use
    def _get_plan(self, stripe_price):
        from readthedocs.subscriptions.models import Plan

        try:
            plan = (
                Plan.objects
                # Exclude "custom" here, as we historically reused Stripe plan
                # id for custom plans. We don't have a better attribute to
                # filter on here.
                .exclude(slug__contains="custom")
                .exclude(name__icontains="Custom")
                .get(stripe_id=stripe_price.id)
            )
            return plan
        except (Plan.DoesNotExist, Plan.MultipleObjectsReturned):
            log.info(
                "Plan lookup failed.",
                stripe_price=stripe_price.id,
            )
        return None


class PlanFeatureManager(models.Manager):

    """Model manager for PlanFeature."""

    # pylint: disable=redefined-builtin
    def get_feature(self, obj, type):
        """
        Get feature `type` for `obj`.

        :param obj: An organization or project instance.
        :param type: The type of the feature (PlanFeature.TYPE_*).
        :returns: A PlanFeature object or None.
        """
        # Avoid circular imports.
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if isinstance(obj, Project):
            organization = obj.organizations.first()
        elif isinstance(obj, Organization):
            organization = obj
        else:
            raise TypeError

        feature = self.filter(
            feature_type=type,
            plan__subscriptions__organization=organization,
        )
        return feature.first()
