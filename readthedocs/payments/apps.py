"""Django app configuration for the payments app."""

import certifi
import stripe
from django.apps import AppConfig


class PaymentsAppConfig(AppConfig):
    name = "readthedocs.payments"
    verbose_name = "Payments"

    def ready(self):
        # stripe-python ships its own CA bundle instead of using certifi,
        # and that bundle still trusts the emSign root behind the compromised
        # eMudhra intermediate CAs (October 2026). Use certifi so Stripe API
        # calls get the same trust store as the rest of our HTTP clients.
        # dj-stripe uses the same module-level setting.
        stripe.ca_bundle_path = certifi.where()
