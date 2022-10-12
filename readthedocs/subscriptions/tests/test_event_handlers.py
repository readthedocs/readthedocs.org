from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.subscriptions import event_handlers
from readthedocs.subscriptions.models import Plan, Subscription


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
class TestStripeEventHandlers(TestCase):

    """Tests for Stripe API endpoint."""

    def setUp(self):
        self.organization = get(Organization, slug="org", email="test@example.com")
        get(Plan, stripe_id="trialing", slug="trialing")

    def test_subscription_updated_event(self):
        """Test handled event."""
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                }
            },
        )
        subscription = get(
            Subscription,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.trialing,
        )
        event_handlers.update_subscription(event=event)

        subscription.refresh_from_db()
        self.assertEqual(subscription.status, SubscriptionStatus.active)
        self.assertEqual(subscription.trial_end_date, end_date)
        self.assertEqual(subscription.end_date, end_date)

    def test_reenabled_organization_on_subscription_updated_event(self):
        """Organization is re-enabled when subscription is active."""
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                }
            },
        )

        organization = get(Organization, disabled=True)
        subscription = get(
            Subscription,
            organization=organization,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.canceled,
        )
        self.assertTrue(organization.disabled)

        event_handlers.update_subscription(event=event)

        subscription.refresh_from_db()
        organization.refresh_from_db()
        self.assertEqual(subscription.status, SubscriptionStatus.active)
        self.assertEqual(subscription.trial_end_date, end_date)
        self.assertEqual(subscription.end_date, end_date)
        self.assertFalse(organization.disabled)

    def test_subscription_deleted_event(self):
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.canceled,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                }
            },
        )
        subscription = get(
            Subscription,
            organization=self.organization,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.active,
        )

        event_handlers.update_subscription(event=event)

        subscription.refresh_from_db()
        self.assertIsNone(subscription.stripe_id)
        self.assertEqual(subscription.status, SubscriptionStatus.canceled)

    def test_subscription_checkout_completed_event(self):
        customer = get(djstripe.Customer, id="cus_KMiHJXFHpLkcRP")
        self.organization.stripe_customer = customer
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "cs_test_a1UpM7pDdpXqqgZC6lQDC2HRMo5d1wW9fNX0ZiBCm6vRqTgZJZx6brwNan",
                    "object": "checkout.session",
                    "customer": customer.id,
                    "subscription": stripe_subscription.id,
                }
            },
        )

        subscription = get(
            Subscription,
            organization=self.organization,
            stripe_id=None,
            status=SubscriptionStatus.canceled,
        )

        event_handlers.checkout_completed(event=event)

        subscription.refresh_from_db()
        self.assertEqual(subscription.stripe_id, stripe_subscription.id)
        self.assertEqual(subscription.status, SubscriptionStatus.active)

    @mock.patch("readthedocs.subscriptions.event_handlers.cancel_stripe_subscription")
    def test_cancel_trial_subscription_after_trial_has_ended(
        self, cancel_subscription_mock
    ):
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=start_date,
        )
        price = get(djstripe.Price, id="trialing")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            subscription=stripe_subscription,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                }
            },
        )
        subscription = get(
            Subscription,
            organization=self.organization,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.active,
        )

        event_handlers.update_subscription(event=event)

        subscription.refresh_from_db()
        self.assertEqual(subscription.status, SubscriptionStatus.active)
        self.assertTrue(subscription.is_trial_ended)
        cancel_subscription_mock.assert_called_once_with(stripe_subscription.id)

    @mock.patch("readthedocs.subscriptions.event_handlers.cancel_stripe_subscription")
    def test_dont_cancel_normal_subscription_after_trial_has_ended(
        self, cancel_subscription_mock
    ):
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=start_date,
        )
        price = get(djstripe.Price, id="advanced")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            subscription=stripe_subscription,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                }
            },
        )
        subscription = get(
            Subscription,
            organization=self.organization,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.active,
        )

        event_handlers.update_subscription(event=event)

        subscription.refresh_from_db()
        self.assertEqual(subscription.status, SubscriptionStatus.active)
        self.assertTrue(subscription.is_trial_ended)
        cancel_subscription_mock.assert_not_called()

    def test_customer_updated_event(self):
        customer = get(
            djstripe.Customer, id="cus_KMiHJXFHpLkcRP", email="new@example.com"
        )
        self.organization.stripe_customer = customer
        self.organization.save()

        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": customer.id,
                    "email": customer.email,
                }
            },
        )

        self.assertNotEqual(self.organization.email, customer.email)

        event_handlers.customer_updated_event(event=event)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.email, customer.email)
