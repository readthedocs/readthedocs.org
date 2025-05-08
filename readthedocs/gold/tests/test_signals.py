import requests_mock
from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase

from ..models import GoldUser
from readthedocs.payments.tests.utils import PaymentMixin


class GoldSignalTests(PaymentMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = fixture.get(User)

    @requests_mock.Mocker(kw="mock_request")
    def test_delete_subscription(self, mock_request):
        subscription = fixture.get(GoldUser, user=self.user, stripe_id="cus_123")
        self.assertIsNotNone(subscription)
        mock_request.get(
            "https://api.stripe.com/v1/customers/cus_123",
            json={"id": "cus_123", "object": "customer"},
        )
        mock_request.delete(
            "https://api.stripe.com/v1/customers/cus_123",
            json={"deleted": True, "customer": "cus_123"},
        )

        subscription.delete()
        assert mock_request.request_history[0]._request.method == "GET"
        assert mock_request.request_history[0]._request.url == "https://api.stripe.com/v1/customers/cus_123"
        assert mock_request.request_history[1]._request.method == "DELETE"
        assert mock_request.request_history[1]._request.url == "https://api.stripe.com/v1/customers/cus_123"
