import requests_mock
from django.test import TestCase

from readthedocs.payments.tests.utils import PaymentMixin
from readthedocs.payments.utils import cancel_subscription


class TestUtils(PaymentMixin, TestCase):

    @requests_mock.Mocker(kw="mock_request")
    def test_cancel_subscription(self, mock_request):
        subscription_id = "sub_1234567890"
        delete_request = mock_request.delete(
            f"https://api.stripe.com/v1/subscriptions/{subscription_id}",
            json={
                "id": subscription_id,
                "object": "subscription",
                "status": "canceled",
            },
        )
        cancel_subscription(subscription_id)
        assert delete_request.called
