import requests_mock
import django_dynamic_fixture as fixture

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..models import GoldUser


class GoldStripeWebhookTests(TestCase):

    EVENT_CHECKOUT_COMPLETED = '''
    {
        "id": "evt_1IQsuoA8fG3kBgfNNG5orMTh",
        "object": "event",
        "api_version": "2020-08-27",
        "created": 1614771054,
        "data": {
            "object": {
                "id": "cs_test_a19ORMf0eP62ZDrd5xQ7V0cn2TcOaxtbnJaFhEigzN4vd3lmSIQ6yTteiL",
                "object": "checkout.session",
                "client_reference_id": "golduser",
                "customer": "cus_a1b2c3",
                "customer_email": "golduser@golduser.com",
                "subscription": "sub_a1b2c3",
                "mode": "subscription"
            }
        },
        "type": "checkout.session.completed"
    }
    '''

    EVENT_CUSTOMER_SUBSCRIPTION_UPDATED = '''
    {
        "id": "evt_1IQsupA8fG3kBgfNgR1SSN0s",
        "object": "event",
        "api_version": "2020-08-27",
        "created": 1614771054,
        "data": {
            "object": {
                "id": "sub_a1b2c3",
                "object": "subscription",
                "customer": "cus_a1b2c3",
                "plan": {
                    "id": "v1-org-15"
                }
            }
        },
        "type": "customer.subscription.updated"
    }
    '''

    def setUp(self):
        self.user = fixture.get(
            User,
            username='golduser'
        )

    @requests_mock.Mocker(kw='mock_request')
    def test_event_checkout_completed(self, mock_request):
        payload = {
            'id': 'sub_a1b2c3',
            'object': 'subscription',
            'customer': 'cus_a1b2c3',
            'plan': {
                'id': 'v1-org-15'
            },
        }
        mock_request.get('https://api.stripe.com/v1/subscriptions/sub_a1b2c3', json=payload)

        self.client.post(
            reverse('api_webhook_stripe'),
            self.EVENT_CHECKOUT_COMPLETED,
            content_type='application/json',
        )

        golduser = GoldUser.objects.get(user__username='golduser')
        self.assertEqual(golduser.level, 'v1-org-15')
        self.assertEqual(golduser.stripe_id, 'cus_a1b2c3')
        self.assertTrue(golduser.subscribed)

    def test_event_subscription_updated(self):
        fixture.get(
            GoldUser,
            user=self.user,
            stripe_id='cus_a1b2c3',
            level='v1-org-5',
            subscribed=True,
        )

        self.client.post(
            reverse('api_webhook_stripe'),
            self.EVENT_CUSTOMER_SUBSCRIPTION_UPDATED,
            content_type='application/json',
        )

        golduser = GoldUser.objects.get(user__username='golduser')
        self.assertEqual(golduser.level, 'v1-org-15')
