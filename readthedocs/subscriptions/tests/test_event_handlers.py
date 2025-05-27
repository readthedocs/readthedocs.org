from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe import webhooks
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.subscriptions import event_handlers
from readthedocs.payments.tests.utils import PaymentMixin
from readthedocs.gold.models import GoldUser


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
class TestStripeEventHandlers(PaymentMixin, TestCase):

    """Tests for Stripe API endpoint."""

    def setUp(self):
        super().setUp()
        self.user = get(User)
        self.organization = get(
            Organization, slug="org", email="test@example.com", owners=[self.user]
        )

    def test_subscription_created_event(self):
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
            customer=customer,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                    "customer": customer.id,
                }
            },
        )

        self.assertIsNone(self.organization.stripe_subscription)
        event_handlers.subscription_created_event(event=event)

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.stripe_subscription, stripe_subscription)

    @mock.patch("readthedocs.subscriptions.event_handlers.cancel_stripe_subscription")
    def test_subscription_updated_event(self, cancel_subscription_mock):
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
        event_handlers.subscription_updated_event(event=event)
        cancel_subscription_mock.assert_not_called()

    def test_reenable_organization_on_subscription_updated_event(self):
        """Organization is re-enabled when subscription is active."""
        customer = get(djstripe.Customer, id="cus_KMiHJXFHpLkcRP")
        self.organization.stripe_customer = customer
        self.organization.disabled = True
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            customer=customer,
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

        self.assertTrue(self.organization.disabled)
        event_handlers.subscription_updated_event(event=event)
        self.organization.refresh_from_db()
        self.assertFalse(self.organization.disabled)

    def test_reenable_organization_on_subscription_created_event(self):
        customer = get(djstripe.Customer, id="cus_KMiHJXFHpLkcRP")
        self.organization.stripe_customer = customer
        self.organization.disabled = True
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            customer=customer,
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                    "customer": customer.id,
                }
            },
        )

        self.assertIsNone(self.organization.stripe_subscription)
        event_handlers.subscription_created_event(event=event)

        self.organization.refresh_from_db()
        self.assertEqual(self.organization.stripe_subscription, stripe_subscription)
        self.assertFalse(self.organization.disabled)

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
            quantity=1,
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

        event_handlers.subscription_updated_event(event=event)
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
            quantity=1,
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

        event_handlers.subscription_updated_event(event=event)
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

    @mock.patch(
        "readthedocs.subscriptions.event_handlers.SubscriptionRequiredNotification.send"
    )
    def test_subscription_canceled_trial_subscription(self, notification_send):
        customer = get(djstripe.Customer)
        self.organization.stripe_customer = customer
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.canceled,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )
        price = get(djstripe.Price, id="trialing")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            quantity=1,
            subscription=stripe_subscription,
        )

        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                }
            },
        )
        event_handlers.subscription_canceled(event)
        event_handlers.subscription_updated_event(event)
        notification_send.assert_called_once()

    @mock.patch(
        "readthedocs.subscriptions.event_handlers.SubscriptionEndedNotification.send"
    )
    def test_subscription_canceled(self, notification_send):
        customer = get(djstripe.Customer)
        self.organization.stripe_customer = customer
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.canceled,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                }
            },
        )
        event_handlers.subscription_canceled(event)
        event_handlers.subscription_updated_event(event)
        notification_send.assert_called_once()

        self.organization.refresh_from_db()
        self.assertTrue(self.organization.disabled)

    @mock.patch(
        "readthedocs.subscriptions.event_handlers.SubscriptionEndedNotification.send"
    )
    def test_subscription_canceled_no_organization_attached(self, notification_send):
        customer = get(djstripe.Customer)

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.canceled,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                }
            },
        )
        event_handlers.subscription_canceled(event)
        event_handlers.subscription_updated_event(event)
        notification_send.assert_not_called()

    @mock.patch(
        "readthedocs.subscriptions.event_handlers.SubscriptionEndedNotification.send"
    )
    def test_subscription_canceled_on_never_disable_organization(self, notification_send):
        customer = get(djstripe.Customer)
        self.organization.stripe_customer = customer
        self.organization.never_disable = True
        self.organization.save()

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_9LtsU02uvjO6Ed",
            status=SubscriptionStatus.canceled,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )
        event = get(
            djstripe.Event,
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                }
            },
        )
        event_handlers.subscription_canceled(event)
        event_handlers.subscription_updated_event(event)

        self.organization.refresh_from_db()
        assert not self.organization.disabled
        notification_send.assert_not_called()

    def test_subscription_precedence(self):
        customer = get(djstripe.Customer, id="cus_KMiHJXFHpLkcRP")
        self.organization.stripe_customer = customer
        self.organization.save()

        assert self.organization.stripe_subscription is None

        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)

        statuses = [
            SubscriptionStatus.canceled,
            SubscriptionStatus.trialing,
            SubscriptionStatus.active,
            SubscriptionStatus.incomplete,
            SubscriptionStatus.incomplete_expired,
            SubscriptionStatus.past_due,
            SubscriptionStatus.unpaid,
        ]
        for i, status in enumerate(statuses):
            stripe_subscription = get(
                djstripe.Subscription,
                id=f"sub_{i}",
                status=status,
                current_period_start=start_date,
                current_period_end=end_date,
                trial_end=end_date,
                customer=customer,
            )
            event = get(
                djstripe.Event,
                data={
                    "object": {
                        "id": stripe_subscription.id,
                        "object": "subscription",
                    }
                },
            )

            event_handlers.subscription_updated_event(event)

            self.organization.refresh_from_db()
            assert self.organization.stripe_subscription == stripe_subscription

    @override_settings(USE_PROMOS=True)
    def test_event_gold_membership_subscription_updated(self):
        stripe_customer_id = "cus_KMiHJXFHpLkcRP"

        golduser = get(
            GoldUser,
            stripe_id=stripe_customer_id,
        )

        customer = get(djstripe.Customer, id=stripe_customer_id)
        status = SubscriptionStatus.active
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)

        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_KMiHJXFHpLkcRP",
            status=status,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )

        price = get(djstripe.Price, id="v1-org-15")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            quantity=1,
            subscription=stripe_subscription,
        )

        event = get(
            djstripe.Event,
            type="customer.subscription.updated",
            data={
                "object": {
                    "id": stripe_subscription.id,
                    "object": "subscription",
                }
            },
        )

        event_handlers.gold_membership_subscription_updated(event)
        golduser = GoldUser.objects.get(stripe_id=stripe_customer_id)
        self.assertEqual(golduser.level, "v1-org-15")


    @override_settings(USE_PROMOS=True)
    def test_event_gold_membership_checkout_completed(self):
        stripe_customer_id = "cus_KMiHJXFHpLkcRP"

        user = get(
            User,
            username="goldusername"
        )
        assert GoldUser.objects.count() == 0

        customer = get(djstripe.Customer, id=stripe_customer_id)
        status = SubscriptionStatus.active
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)

        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_KMiHJXFHpLkcRP",
            status=status,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
            customer=customer,
        )

        price = get(djstripe.Price, id="v1-org-15")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            quantity=1,
            subscription=stripe_subscription,
        )

        event = get(
            djstripe.Event,
            type="checkout.session.completed",
            data={
                "object": {
                    "id": "cs_a11YYuvkDjsA",
                    "object": "checkout.session",
                    "mode": "subscription",
                    "client_reference_id": "goldusername",
                    "subscription": "sub_KMiHJXFHpLkcRP",
                }
            },
        )

        event_handlers.gold_membership_new_subscription(event)

        golduser = GoldUser.objects.get(stripe_id=stripe_customer_id)
        self.assertEqual(GoldUser.objects.count(), 1)
        self.assertEqual(golduser.level, "v1-org-15")
        self.assertEqual(golduser.stripe_id, stripe_customer_id)
        self.assertTrue(golduser.subscribed)
