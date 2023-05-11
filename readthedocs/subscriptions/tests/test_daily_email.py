from datetime import timedelta
from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization, OrganizationOwner
from readthedocs.subscriptions.models import Subscription
from readthedocs.subscriptions.tasks import daily_email


@mock.patch('readthedocs.notifications.backends.send_email')
@mock.patch('readthedocs.notifications.storages.FallbackUniqueStorage')
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

    def test_organization_disabled(self, mock_storage_class, mock_send_email):
        """Subscription ended ``DISABLE_AFTER_DAYS`` days ago daily email."""
        sub1 = fixture.get(
            Subscription,
            status='past_due',
            end_date=timezone.now() - timedelta(days=30),
        )
        owner1 = fixture.get(
            OrganizationOwner,
            organization=sub1.organization,
        )

        sub2 = fixture.get(
            Subscription,
            status='past_due',
            end_date=timezone.now() - timedelta(days=35),
        )
        owner2 = fixture.get(
            OrganizationOwner,
            organization=sub2.organization,
        )

        mock_storage = mock.Mock()
        mock_storage_class.return_value = mock_storage

        daily_email()

        self.assertEqual(mock_storage.add.call_count, 1)
        mock_storage.add.assert_has_calls([
            mock.call(
                message=mock.ANY,
                extra_tags='',
                level=31,
                user=owner1.owner,
            ),
        ])
        self.assertEqual(mock_send_email.call_count, 1)
        mock_send_email.assert_has_calls([
            mock.call(
                subject='Your Read the Docs organization will be disabled soon',
                recipient=owner1.owner.email,
                template=mock.ANY,
                template_html=mock.ANY,
                context=mock.ANY,
            ),
        ])
