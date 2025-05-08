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
