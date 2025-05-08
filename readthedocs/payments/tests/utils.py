from djstripe.models import APIKey
from djstripe.enums import APIKeyType


class PaymentMixin:

    def setUp(self):
        APIKey.objects.create(type=APIKeyType.PUBLISHABLE, livemode=False, secret="pk_test_")
        APIKey.objects.create(type=APIKeyType.SECRET, livemode=False, secret="sk_test_")
