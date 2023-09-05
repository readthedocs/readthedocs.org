from datetime import timedelta
from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import InvoiceStatus, SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.tasks import (
    daily_email,
    disable_organization_expired_trials,
)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
@mock.patch("readthedocs.notifications.backends.send_email")
@mock.patch("readthedocs.notifications.storages.FallbackUniqueStorage")
class DailyEmailTests(TestCase):
    def test_trial_ending(self, mock_storage_class, mock_send_email):
        """Trial ending daily email."""
        now = timezone.now()

        owner1 = get(User)
        org1 = get(Organization, owners=[owner1])
        customer1 = get(djstripe.Customer)
        org1.stripe_customer = customer1
        org1.save()
        get(
            djstripe.Subscription,
            status=SubscriptionStatus.trialing,
            trial_start=now,
            trial_end=now + timedelta(days=7),
            created=now - timedelta(days=24),
            customer=customer1,
        )

        owner2 = get(User)
        org2 = fixture.get(Organization, owners=[owner2])
        customer2 = get(djstripe.Customer)
        org2.stripe_customer = customer2
        org2.save()
        get(
            djstripe.Subscription,
            status=SubscriptionStatus.trialing,
            trial_start=now,
            trial_end=now + timedelta(days=7),
            created=now - timedelta(days=25),
        )

        mock_storage = mock.Mock()
        mock_storage_class.return_value = mock_storage

        daily_email()

        self.assertEqual(mock_storage.add.call_count, 1)
        mock_storage.add.assert_has_calls(
            [
                mock.call(
                    message=mock.ANY,
                    extra_tags="",
                    level=31,
                    user=owner1,
                ),
            ]
        )
        self.assertEqual(mock_send_email.call_count, 1)
        mock_send_email.assert_has_calls(
            [
                mock.call(
                    subject="Your trial is ending soon",
                    recipient=owner1.email,
                    template=mock.ANY,
                    template_html=mock.ANY,
                    context=mock.ANY,
                ),
            ]
        )

    def test_organizations_to_be_disable_email(
        self, mock_storage_class, mock_send_email
    ):
        """Subscription ended ``DISABLE_AFTER_DAYS`` days ago daily email."""
        customer1 = get(djstripe.Customer)
        latest_invoice1 = get(
            djstripe.Invoice,
            due_date=timezone.now() - timedelta(days=30),
            status=InvoiceStatus.open,
        )
        sub1 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.past_due,
            latest_invoice=latest_invoice1,
            customer=customer1,
        )
        owner1 = get(User)
        get(
            Organization,
            owners=[owner1],
            stripe_customer=customer1,
            stripe_subscription=sub1,
        )

        customer2 = get(djstripe.Customer)
        latest_invoice2 = get(
            djstripe.Invoice,
            due_date=timezone.now() - timedelta(days=35),
            status=InvoiceStatus.open,
        )
        sub2 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.past_due,
            latest_invoice=latest_invoice2,
            customer=customer2,
        )
        owner2 = get(User)
        get(
            Organization,
            owners=[owner2],
            stripe_customer=customer2,
            stripe_subscription=sub2,
        )

        mock_storage = mock.Mock()
        mock_storage_class.return_value = mock_storage

        daily_email()

        self.assertEqual(mock_storage.add.call_count, 1)
        mock_storage.add.assert_has_calls(
            [
                mock.call(
                    message=mock.ANY,
                    extra_tags="",
                    level=31,
                    user=owner1,
                ),
            ]
        )
        self.assertEqual(mock_send_email.call_count, 1)
        mock_send_email.assert_has_calls(
            [
                mock.call(
                    subject="Your Read the Docs organization will be disabled soon",
                    recipient=owner1.email,
                    template=mock.ANY,
                    template_html=mock.ANY,
                    context=mock.ANY,
                ),
            ]
        )


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
class SubscriptionTasksTests(TestCase):
    def test_disable_organizations_with_expired_trial(self):
        price = get(djstripe.Price, id="trialing")

        # Active trial subscription
        subscription1 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.active,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=price,
            quantity=1,
            subscription=subscription1,
        )
        organization_with_active_subscription = get(
            Organization,
            stripe_subscription=subscription1,
            stripe_customer=subscription1.customer,
        )

        # Canceled trial subscription
        subscription2 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.canceled,
            customer=get(djstripe.Customer),
            ended_at=timezone.now() - timedelta(days=30),
        )
        get(
            djstripe.SubscriptionItem,
            price=price,
            quantity=1,
            subscription=subscription2,
        )
        organization_with_canceled_trial_subscription = get(
            Organization,
            stripe_subscription=subscription2,
            stripe_customer=subscription2.customer,
        )

        # Canceled subscription
        subscription3 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.canceled,
            customer=get(djstripe.Customer),
            ended_at=timezone.now() - timedelta(days=30),
        )
        get(
            djstripe.SubscriptionItem,
            quantity=1,
            subscription=subscription3,
        )
        organization_with_canceled_subscription = get(
            Organization,
            stripe_subscription=subscription3,
            stripe_customer=subscription3.customer,
        )

        disable_organization_expired_trials()

        organization_with_active_subscription.refresh_from_db()
        self.assertFalse(organization_with_active_subscription.disabled)

        organization_with_canceled_trial_subscription.refresh_from_db()
        self.assertTrue(organization_with_canceled_trial_subscription.disabled)

        organization_with_canceled_subscription.refresh_from_db()
        self.assertFalse(organization_with_canceled_subscription.disabled)
