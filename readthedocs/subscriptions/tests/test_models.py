import django_dynamic_fixture as fixture
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from django_dynamic_fixture.ddf import BadDataError
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus

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
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_foo",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        price = get(djstripe.Price, id="advanced")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            subscription=stripe_subscription,
        )

        subscription = fixture.get(
            Subscription,
            stripe_id=stripe_subscription.id,
            status=SubscriptionStatus.trialing,
        )
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(
            subscription.end_date,
            end_date,
        )
        self.assertEqual(
            subscription.trial_end_date,
            end_date,
        )

        # Cancel event
        stripe_subscription.status = SubscriptionStatus.unpaid
        stripe_subscription.save()
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'unpaid')
        self.assertEqual(
            subscription.trial_end_date,
            end_date,
        )

    def test_replace_subscription(self):
        """Test update from stripe."""
        start_date = timezone.now()
        end_date = timezone.now() + timezone.timedelta(days=30)
        stripe_subscription = get(
            djstripe.Subscription,
            id="sub_bar",
            status=SubscriptionStatus.active,
            current_period_start=start_date,
            current_period_end=end_date,
            trial_end=end_date,
        )
        price = get(djstripe.Price, id="advanced")
        get(
            djstripe.SubscriptionItem,
            id="si_KOcEsHCktPUedU",
            price=price,
            subscription=stripe_subscription,
        )

        subscription = fixture.get(
            Subscription,
            stripe_id='sub_foo',
            status=SubscriptionStatus.trialing,
        )
        Subscription.objects.update_from_stripe(
            rtd_subscription=subscription,
            stripe_subscription=stripe_subscription,
        )
        subscription.refresh_from_db()
        self.assertEqual(subscription.stripe_id, 'sub_bar')
        self.assertEqual(subscription.status, 'active')
