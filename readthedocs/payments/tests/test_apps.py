import certifi
import stripe
from django.test import TestCase


class TestPaymentsAppConfig(TestCase):
    def test_stripe_uses_certifi_ca_bundle(self):
        assert stripe.ca_bundle_path == certifi.where()
