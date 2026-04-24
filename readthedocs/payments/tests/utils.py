from djstripe.models import APIKey
from djstripe.enums import APIKeyType
from djstripe.models import Account

class PaymentMixin:

    def setUp(self):
        super().setUp()

        Account.objects.create(
            id="acct_1032D82eZvKYlo2C",
            charges_enabled=True,
            country="US",
            default_currency="USD",
            details_submitted=True,
            email="testing@readthedocs.org",
            type="standard",
        )
        APIKey.objects.create(type=APIKeyType.publishable, livemode=False, secret="pk_test_")
        APIKey.objects.create(type=APIKeyType.secret, livemode=False, secret="sk_test_")
