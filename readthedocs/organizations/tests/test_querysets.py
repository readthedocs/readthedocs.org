from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import InvoiceStatus, SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.payments.tests.utils import PaymentMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE="trialing",
)
class TestOrganizationQuerysets(PaymentMixin, TestCase):

    def test_only_owner(self):
        user = get(User)
        another_user = get(User)

        org_one = get(Organization, slug="one", owners=[user])
        org_two = get(Organization, slug="two", owners=[user])
        org_three = get(Organization, slug="three", owners=[another_user])
        get(Organization, slug="four", owners=[user, another_user])
        get(Organization, slug="five", owners=[])

        self.assertEqual(
            {org_one, org_two}, set(Organization.objects.single_owner(user))
        )
        self.assertEqual(
            {org_three}, set(Organization.objects.single_owner(another_user))
        )

    def test_on_trial(self):
        trial_price = get(djstripe.Price, id="trialing")
        paid_price = get(djstripe.Price, id="advanced")

        # Organization on the trial plan, still within its trial period.
        trialing_subscription = get(
            djstripe.Subscription,
            status=SubscriptionStatus.trialing,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=trial_price,
            quantity=1,
            subscription=trialing_subscription,
        )
        org_on_trial = get(
            Organization,
            stripe_subscription=trialing_subscription,
            stripe_customer=trialing_subscription.customer,
        )

        # Organization with a trial plan subscription that was canceled.
        canceled_subscription = get(
            djstripe.Subscription,
            status=SubscriptionStatus.canceled,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=trial_price,
            quantity=1,
            subscription=canceled_subscription,
        )
        org_trial_ended = get(
            Organization,
            stripe_subscription=canceled_subscription,
            stripe_customer=canceled_subscription.customer,
        )

        # Organization with a paid plan subscription within its trial period.
        paid_trialing_subscription = get(
            djstripe.Subscription,
            status=SubscriptionStatus.trialing,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=paid_price,
            quantity=1,
            subscription=paid_trialing_subscription,
        )
        org_paid_trialing = get(
            Organization,
            stripe_subscription=paid_trialing_subscription,
            stripe_customer=paid_trialing_subscription.customer,
        )

        assert list(Organization.objects.on_trial()) == [org_on_trial]

    def test_organizations_with_trial_subscription_plan_ended(self):
        price = get(djstripe.Price, id="trialing")

        stripe_subscription1 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.active,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=price,
            quantity=1,
            subscription=stripe_subscription1,
        )

        org1 = get(
            Organization,
            stripe_subscription=stripe_subscription1,
            stripe_customer=stripe_subscription1.customer,
        )

        stripe_subscription2 = get(
            djstripe.Subscription,
            status=SubscriptionStatus.canceled,
            customer=get(djstripe.Customer),
        )
        get(
            djstripe.SubscriptionItem,
            price=price,
            quantity=1,
            subscription=stripe_subscription2,
        )
        org2 = get(
            Organization,
            stripe_subscription=stripe_subscription2,
            stripe_customer=stripe_subscription2.customer,
        )

        self.assertEqual(
            list(Organization.objects.subscription_trial_plan_ended()), [org2]
        )

    def test_organizations_to_be_disabled(self):
        subscription1 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.active,
        )
        organization_active = get(
            Organization,
            stripe_subscription=subscription1,
            stripe_customer=subscription1.customer,
        )

        subscription2 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=30),
        )
        organization_canceled_30_days_ago = get(
            Organization,
            stripe_subscription=subscription2,
            stripe_customer=subscription2.customer,
        )

        subscription3 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now(),
        )
        organization_canceled_now = get(
            Organization,
            stripe_subscription=subscription3,
            stripe_customer=subscription3.customer,
        )

        subscription4 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=35),
        )
        organization_canceled_35_days_ago = get(
            Organization,
            stripe_subscription=subscription4,
            stripe_customer=subscription4.customer,
        )

        latest_invoice1 = get(
            djstripe.Invoice,
            due_date=timezone.now() + timedelta(days=30),
            status=InvoiceStatus.open,
        )
        subscription5 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.past_due,
            latest_invoice=latest_invoice1,
        )
        organization_past_due_in_30_days = get(
            Organization,
            stripe_subscription=subscription5,
            stripe_customer=subscription5.customer,
        )

        latest_invoice2 = get(
            djstripe.Invoice,
            due_date=timezone.now() - timedelta(days=30),
            status=InvoiceStatus.open,
        )
        subscription6 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.past_due,
            latest_invoice=latest_invoice2,
        )
        organization_past_due_30_days_ago = get(
            Organization,
            stripe_subscription=subscription6,
            stripe_customer=subscription6.customer,
        )

        latest_invoice3 = get(
            djstripe.Invoice,
            due_date=timezone.now() - timedelta(days=35),
            status=InvoiceStatus.open,
        )
        subscription7 = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.past_due,
            latest_invoice=latest_invoice3,
        )
        organization_past_due_35_days_ago = get(
            Organization,
            stripe_subscription=subscription7,
            stripe_customer=subscription7.customer,
        )

        self.assertEqual(
            set(Organization.objects.disable_soon(days=30, exact=False)),
            {organization_canceled_35_days_ago, organization_past_due_35_days_ago},
        )

        self.assertEqual(
            set(Organization.objects.disable_soon(days=20, exact=False)),
            {
                organization_canceled_30_days_ago,
                organization_canceled_35_days_ago,
                organization_past_due_35_days_ago,
                organization_past_due_30_days_ago,
            },
        )

        self.assertEqual(
            set(Organization.objects.disable_soon(days=30, exact=True)),
            {organization_canceled_30_days_ago, organization_past_due_30_days_ago},
        )

        self.assertEqual(
            set(Organization.objects.disable_soon(days=35, exact=True)),
            {organization_canceled_35_days_ago, organization_past_due_35_days_ago},
        )

        self.assertEqual(
            set(Organization.objects.disable_soon(days=20, exact=True)),
            set(),
        )

        organization_past_due_30_days_ago.disabled = True
        organization_past_due_30_days_ago.save()
        self.assertEqual(
            set(Organization.objects.disable_soon(days=30, exact=False)),
            {organization_canceled_35_days_ago, organization_past_due_35_days_ago},
        )

        organization_past_due_30_days_ago.disabled = False
        organization_past_due_30_days_ago.never_disable = True
        organization_past_due_30_days_ago.save()
        self.assertEqual(
            set(Organization.objects.disable_soon(days=30, exact=False)),
            {organization_canceled_35_days_ago, organization_past_due_35_days_ago},
        )

    def test_organizations_disable_serving(self):
        subscription_active = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.active,
        )
        get(
            Organization,
            stripe_subscription=subscription_active,
            stripe_customer=subscription_active.customer,
        )

        # Disabled recently: keep serving docs during the grace window.
        subscription_ended_35_days_ago = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=35),
        )
        get(
            Organization,
            disabled=True,
            stripe_subscription=subscription_ended_35_days_ago,
            stripe_customer=subscription_ended_35_days_ago.customer,
        )

        # Subscription ended long ago, but the organization was never
        # marked as disabled (e.g. never_disable): keep serving docs.
        subscription_ended_100_days_ago = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=100),
        )
        get(
            Organization,
            disabled=False,
            stripe_subscription=subscription_ended_100_days_ago,
            stripe_customer=subscription_ended_100_days_ago.customer,
        )

        subscription_ended_100_days_ago_disabled = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=100),
        )
        organization_long_disabled = get(
            Organization,
            disabled=True,
            stripe_subscription=subscription_ended_100_days_ago_disabled,
            stripe_customer=subscription_ended_100_days_ago_disabled.customer,
        )

        # Artifacts already cleaned: serving is still disabled.
        subscription_ended_100_days_ago_cleaned = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=100),
        )
        organization_long_disabled_cleaned = get(
            Organization,
            disabled=True,
            artifacts_cleaned=True,
            stripe_subscription=subscription_ended_100_days_ago_cleaned,
            stripe_customer=subscription_ended_100_days_ago_cleaned.customer,
        )

        assert set(Organization.objects.disable_serving()) == {
            organization_long_disabled,
            organization_long_disabled_cleaned,
        }

    def test_organizations_clean_artifacts(self):
        subscription_ended_100_days_ago = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=100),
        )
        organization_long_disabled = get(
            Organization,
            disabled=True,
            stripe_subscription=subscription_ended_100_days_ago,
            stripe_customer=subscription_ended_100_days_ago.customer,
        )

        # Artifacts already cleaned: nothing left to clean.
        subscription_ended_100_days_ago_cleaned = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=100),
        )
        get(
            Organization,
            disabled=True,
            artifacts_cleaned=True,
            stripe_subscription=subscription_ended_100_days_ago_cleaned,
            stripe_customer=subscription_ended_100_days_ago_cleaned.customer,
        )

        assert set(Organization.objects.clean_artifacts()) == {
            organization_long_disabled,
        }
