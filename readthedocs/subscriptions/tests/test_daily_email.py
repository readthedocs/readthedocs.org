from datetime import timedelta
from unittest import mock

import django_dynamic_fixture as fixture
from django.test import TestCase
from django.utils import timezone

from readthedocs.organizations.models import Organization, OrganizationOwner
from readthedocs.subscriptions.models import Subscription
from readthedocs.subscriptions.tasks import daily_email


@mock.patch('readthedocs.notifications.backends.send_email')
@mock.patch('readthedocs.notifications.storages.FallbackUniqueStorage')
class DailyEmailTests(TestCase):

    def test_trial_ending(self, mock_storage_class, mock_send_email):
        """Trial ending daily email."""
        org1 = fixture.get(
            Organization,
            pub_date=timezone.now() - timedelta(days=24),
            subscription=None,
        )
        owner1 = fixture.get(
            OrganizationOwner,
            organization=org1,
        )
        org2 = fixture.get(
            Organization,
            pub_date=timezone.now() - timedelta(days=25),
            subscription=None,
        )
        owner2 = fixture.get(
            OrganizationOwner,
            organization=org2,
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
                request=mock.ANY,
                subject='Your trial is ending soon',
                recipient=owner1.owner.email,
                template=mock.ANY,
                template_html=mock.ANY,
                context=mock.ANY,
            ),
        ])

    def test_trial_ended(self, mock_storage_class, mock_send_email):
        """Trial ended daily email."""
        org1 = fixture.get(
            Organization,
            pub_date=timezone.now() - timedelta(days=30),
            subscription=None,
        )
        owner1 = fixture.get(
            OrganizationOwner,
            organization=org1,
        )
        org2 = fixture.get(
            Organization,
            pub_date=timezone.now() - timedelta(days=31),
            subscription=None,
        )
        owner2 = fixture.get(
            OrganizationOwner,
            organization=org2,
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
                request=mock.ANY,
                subject='We hope you enjoyed your trial of Read the Docs!',
                recipient=owner1.owner.email,
                template=mock.ANY,
                template_html=mock.ANY,
                context=mock.ANY,
            ),
        ])

    def test_subscription_ended_days_ago(
            self,
            mock_storage_class,
            mock_send_email,
    ):
        """Subscription ended some days ago daily email."""
        sub1 = fixture.get(
            Subscription,
            status='past_due',
            end_date=timezone.now() - timedelta(days=5),
        )
        owner1 = fixture.get(
            OrganizationOwner,
            organization=sub1.organization,
        )

        sub2 = fixture.get(
            Subscription,
            status='past_due',
            end_date=timezone.now() - timedelta(days=3),
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
                request=mock.ANY,
                subject='Your subscription to Read the Docs has ended',
                recipient=owner1.owner.email,
                template=mock.ANY,
                template_html=mock.ANY,
                context=mock.ANY,
            ),
        ])

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
                request=mock.ANY,
                subject='Your Read the Docs organization will be disabled soon',
                recipient=owner1.owner.email,
                template=mock.ANY,
                template_html=mock.ANY,
                context=mock.ANY,
            ),
        ])
