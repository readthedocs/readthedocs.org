from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from djstripe import models as djstripe

from readthedocs.organizations.models import Organization
from readthedocs.payments.tests.utils import PaymentMixin


class TestSignals(PaymentMixin, TestCase):
    def setUp(self):
        super().setUp()
        email = "test@example.com"

        self.user = get(User)
        self.stripe_customer = get(
            djstripe.Customer,
            email=email,
            name="org",
        )
        self.organization = get(
            Organization,
            slug="org",
            name="org",
            owners=[self.user],
            email=email,
            stripe_customer=self.stripe_customer,
        )
        self.stripe_customer.metadata = self.organization.get_stripe_metadata()
        self.stripe_customer.description = self.organization.name
        self.stripe_customer.save()

    @mock.patch("readthedocs.subscriptions.signals.get_stripe_client")
    def test_update_organization_email(self, stripe_client):
        new_email = "new@example.com"
        self.organization.email = new_email
        self.organization.save()
        stripe_client().customers.update.assert_called_once_with(
            self.stripe_customer.id,
            params={
                "email": new_email,
            },
        )

    @mock.patch("readthedocs.subscriptions.signals.get_stripe_client")
    def test_update_organization_name(self, stripe_client):
        new_name = "New organization"
        self.organization.name = new_name
        self.organization.save()
        stripe_client().customers.update.assert_called_once_with(
            self.stripe_customer.id,
            params={
                "description": new_name,
                "name": self.organization.name,
            },
        )

    @mock.patch("readthedocs.subscriptions.signals.get_stripe_client")
    def test_update_organization_slug(self, stripe_client):
        new_slug = "new-org"
        self.organization.slug = new_slug
        self.organization.save()
        new_metadata = self.organization.get_stripe_metadata()
        stripe_client().customers.update.assert_called_once_with(
            self.stripe_customer.id,
            params={
                "metadata": new_metadata,
            },
        )

    @mock.patch("readthedocs.subscriptions.signals.get_stripe_client")
    def test_save_organization_no_changes(self, stripe_client):
        self.organization.save()
        stripe_client().customers.update.assert_not_called()
