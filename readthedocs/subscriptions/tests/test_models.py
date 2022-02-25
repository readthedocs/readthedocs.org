from datetime import datetime

import django_dynamic_fixture as fixture
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture.ddf import BadDataError
from stripe import Subscription as StripeSubscription

from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.models import Plan, Subscription


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class SubscriptionTests(TestCase):

    def setUp(self):
        fixture.get(
            Plan,
            stripe_id='basic',
        )
        fixture.get(
            Plan,
            stripe_id='advanced',
        )

    def test_create(self):
        """Subscription creation."""
        org = fixture.get(Organization)
        subscription = fixture.get(Subscription, organization=org)
        self.assertIsNotNone(subscription)
        self.assertIsNotNone(org.subscription)

    def test_double_create(self):
        """Subscription creation."""
        org = fixture.get(Organization)
        fixture.get(Subscription, organization=org)
        with self.assertRaises(BadDataError):
            fixture.get(Subscription, organization=org)

    def test_delete(self):
        """Subscription delete doesn't cascade."""
        org = fixture.get(Organization)
        subscription = fixture.get(Subscription, organization=org)
        self.assertIsNotNone(subscription)
        self.assertIsNotNone(org.subscription)

        Subscription.objects.filter(organization=org).delete()
        org = Organization.objects.get(slug=org.slug)
        self.assertIsNotNone(org)

    def test_update(self):
        """Test update from stripe."""
        stripe_subscription = StripeSubscription.construct_from(
            {
                'id': 'sub_foo',
                'status': 'active',
                'current_period_start': 120778389,
                'current_period_end': 123456789,
                'trial_end': 1475437877,
                'plan': {
                    'id': 'advanced',
                }
            },
            None,
        )
        subscription = fixture.get(
            Subscription,
            stripe_id='sub_foo',
            status='trialing',
        )
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(
            subscription.end_date,
            timezone.make_aware(datetime.fromtimestamp(123456789)),
        )
        self.assertEqual(
            subscription.trial_end_date,
            timezone.make_aware(datetime.fromtimestamp(1475437877)),
        )

        # Cancel event
        stripe_subscription = StripeSubscription.construct_from(
            {
                'id': 'sub_foo',
                'status': 'unpaid',
                'plan': {
                    'id': 'advanced',
                }
            },
            None,
        )
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'unpaid')
        self.assertEqual(
            subscription.trial_end_date,
            timezone.make_aware(datetime.fromtimestamp(1475437877)),
        )

    def test_replace_subscription(self):
        """Test update from stripe."""
        stripe_subscription = StripeSubscription.construct_from(
            {
                'id': 'sub_bar',
                'status': 'active',
                'plan': {
                    'id': 'advanced',
                }
            },
            None,
        )
        subscription = fixture.get(
            Subscription,
            stripe_id='sub_foo',
            status='trialing',
        )
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.stripe_id, 'sub_bar')
        self.assertEqual(subscription.status, 'active')
