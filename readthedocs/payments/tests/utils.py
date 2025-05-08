from djstripe.models import APIKey
from djstripe.enums import APIKeyType


class PaymentMixin:

    def setUp(self):
        APIKey.objects.create(type=APIKeyType.publishable, livemode=False, secret="pk_test_")
        APIKey.objects.create(type=APIKeyType.secret, livemode=False, secret="sk_test_")
