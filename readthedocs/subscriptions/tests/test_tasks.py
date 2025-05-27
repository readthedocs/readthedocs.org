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
from readthedocs.subscriptions.tasks import daily_email
from readthedocs.payments.tests.utils import PaymentMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
@mock.patch("readthedocs.notifications.email.send_email")
class DailyEmailTests(PaymentMixin, TestCase):

    def test_trial_ending(self, mock_send_email):
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

        daily_email()

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

    def test_organizations_to_be_disabled_email(self, mock_send_email):
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

        daily_email()

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
