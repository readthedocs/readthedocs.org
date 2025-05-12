from unittest import mock

import requests_mock
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus

from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.constants import (
    TYPE_CONCURRENT_BUILDS,
    TYPE_PRIVATE_DOCS,
)
from readthedocs.subscriptions.products import RTDProduct, RTDProductFeature
from readthedocs.payments.tests.utils import PaymentMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_PRODUCTS=dict(
        [
            RTDProduct(
                stripe_id="prod_a1b2c3",
                listed=True,
                features=dict(
                    [
                        RTDProductFeature(
                            type=TYPE_PRIVATE_DOCS,
                        ).to_item(),
                    ]
                ),
            ).to_item(),
            RTDProduct(
                stripe_id="prod_extra_builder",
                extra=True,
                features=dict(
                    [RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=1).to_item()]
                ),
            ).to_item(),
        ]
    ),
)
class SubscriptionViewTests(PaymentMixin, TestCase):

    """Subscription view tests."""

    def setUp(self):
        super().setUp()
        self.user = get(User)
        self.organization = get(Organization, stripe_id="123", owners=[self.user])
        self.stripe_product = get(
            djstripe.Product,
            id="prod_a1b2c3",
        )
        self.stripe_price = get(
            djstripe.Price,
            id=settings.RTD_ORG_DEFAULT_STRIPE_SUBSCRIPTION_PRICE,
            unit_amount=50000,
            product=self.stripe_product,
        )
        self.extra_product = get(
            djstripe.Product,
            id="prod_extra_builder",
        )
        self.extra_price = get(
            djstripe.Price,
            id="price_extra_builder",
            unit_amount=50000,
            product=self.extra_product,
        )
        self.stripe_subscription = self._create_stripe_subscription(
            customer_id=self.organization.stripe_id,
            subscription_id="sub_a1b2c3d4",
        )
        self.stripe_customer = self.stripe_subscription.customer

        self.organization.stripe_customer = self.stripe_customer
        self.organization.stripe_subscription = self.stripe_subscription
        self.organization.save()
        self.client.force_login(self.user)

    def _create_stripe_subscription(
        self, customer_id="cus_a1b2c3", subscription_id="sub_a1b2c3"
    ):
        stripe_customer = get(
            djstripe.Customer,
            id=customer_id,
        )
        stripe_subscription = get(
            djstripe.Subscription,
            id=subscription_id,
            start_date=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            trial_end=timezone.now() + timezone.timedelta(days=30),
            status=SubscriptionStatus.active,
            customer=stripe_customer,
        )
        get(
            djstripe.SubscriptionItem,
            price=self.stripe_price,
            quantity=1,
            subscription=stripe_subscription,
        )
        return stripe_subscription

    def test_active_subscription(self):
        resp = self.client.get(
            reverse("subscription_detail", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["stripe_subscription"], self.stripe_subscription)
        self.assertContains(resp, "active")
        self.assertNotContains(resp, "Extra products:")
        # The subscribe form isn't shown, but the manage susbcription button is.
        self.assertContains(resp, "Manage subscription")
        self.assertNotContains(resp, "Start subscription")

    def test_active_subscription_with_extra_product(self):
        get(
            djstripe.SubscriptionItem,
            price=self.extra_price,
            quantity=2,
            subscription=self.stripe_subscription,
        )
        resp = self.client.get(
            reverse("subscription_detail", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["stripe_subscription"], self.stripe_subscription)
        self.assertContains(resp, "active")
        self.assertContains(resp, "Extra products:")
        # The subscribe form isn't shown, but the manage susbcription button is.
        self.assertContains(resp, "Manage subscription")
        self.assertNotContains(resp, "Start subscription")

    @requests_mock.Mocker(kw="mock_request")
    def test_manage_subscription(self, mock_request):
        payload = {
            "url": "https://billing.stripe.com/session/a1b2c3",
        }
        mock_request.post(
            "https://api.stripe.com/v1/billing_portal/sessions", json=payload
        )
        response = self.client.post(
            reverse(
                "stripe_customer_portal",
                kwargs={"slug": self.organization.slug},
            ),
        )
        self.assertRedirects(
            response,
            payload.get("url"),
            fetch_redirect_response=False,
        )

    @mock.patch("readthedocs.subscriptions.utils.get_stripe_client")
    def test_user_without_subscription(self, stripe_client):
        stripe_subscription = self._create_stripe_subscription()
        stripe_customer = stripe_subscription.customer
        stripe_customer.subscribe = mock.MagicMock()
        stripe_customer.subscribe.return_value = stripe_subscription

        self.organization.refresh_from_db()
        self.organization.stripe_customer = stripe_customer
        self.organization.stripe_subscription = None
        self.organization.save()
        self.assertFalse(hasattr(self.organization, "subscription"))
        self.assertIsNone(self.organization.stripe_subscription)

        resp = self.client.get(
            reverse("subscription_detail", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 200)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.stripe_customer, stripe_customer)
        self.assertEqual(self.organization.stripe_subscription, stripe_subscription)
        stripe_client().assert_not_called()

    @mock.patch(
        "readthedocs.subscriptions.utils.djstripe.Customer.sync_from_stripe_data"
    )
    @mock.patch("readthedocs.subscriptions.utils.get_stripe_client")
    def test_user_without_subscription_and_customer(
        self, stripe_client, sync_from_stripe_data_mock
    ):
        stripe_subscription = self._create_stripe_subscription()
        stripe_customer = stripe_subscription.customer
        stripe_customer.subscribe = mock.MagicMock()
        stripe_customer.subscribe.return_value = stripe_subscription
        sync_from_stripe_data_mock.return_value = stripe_customer

        # When stripe_customer is None, a new customer is created.
        self.organization.stripe_customer = None
        self.organization.stripe_subscription = None
        self.organization.save()
        self.organization.refresh_from_db()
        self.assertFalse(hasattr(self.organization, "subscription"))
        self.assertIsNone(self.organization.stripe_customer)
        self.assertIsNone(self.organization.stripe_subscription)

        resp = self.client.get(
            reverse("subscription_detail", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 200)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.stripe_id, "cus_a1b2c3")
        self.assertEqual(self.organization.stripe_customer, stripe_customer)
        self.assertEqual(self.organization.stripe_subscription, stripe_subscription)
        stripe_client().customers.create.assert_called_once()

    def test_user_with_canceled_subscription(self):
        self.stripe_subscription.status = SubscriptionStatus.canceled
        self.stripe_subscription.save()
        resp = self.client.get(
            reverse("subscription_detail", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["stripe_subscription"], self.stripe_subscription)
        # The Manage subscription form isn't shown, but the Subscribe is.
        self.assertNotContains(resp, "Manage subscription")
        self.assertContains(resp, "Start subscription")
