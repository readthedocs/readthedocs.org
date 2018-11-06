from __future__ import absolute_import
import mock
import django_dynamic_fixture as fixture
from django.test import TestCase
from django.contrib.auth.models import User

from readthedocs.projects.models import Project

from ..models import GoldUser
from ..forms import GoldSubscriptionForm


class GoldSubscriptionFormTests(TestCase):

    def setUp(self):
        self.owner = fixture.get(User)
        self.user = fixture.get(User)
        self.project = fixture.get(Project, users=[self.user])

        # Mocking
        self.patches = {}
        self.mocks = {}
        self.patches['requestor'] = mock.patch('stripe.api_requestor.APIRequestor')

        for patch in self.patches:
            self.mocks[patch] = self.patches[patch].start()

        self.mocks['request'] = self.mocks['requestor'].return_value
        self.mock_request([({}, 'reskey')])

    def mock_request(self, resp):
        self.mocks['request'].request = mock.Mock(side_effect=resp)

    def test_add_subscription(self):
        """Valid subscription form"""
        subscription_list = {
            'object': 'list',
            'data': [],
            'has_more': False,
            'total_count': 1,
            'url': '/v1/customers/cus_12345/subscriptions',
        }
        customer_obj = {
            'id': 'cus_12345',
            'description': self.user.get_full_name(),
            'email': self.user.email,
            'subscriptions': subscription_list
        }
        subscription_obj = {
            'id': 'sub_12345',
            'object': 'subscription',
            'customer': 'cus_12345',
            'plan': {
                'id': 'v1-org-5',
                'object': 'plan',
                'amount': 1000,
                'currency': 'usd',
                'name': 'Test',
            }
        }
        self.mock_request([
            (customer_obj, ''),
            (subscription_list, ''),
            (subscription_obj, ''),
        ])

        # Create user and subscription
        subscription_form = GoldSubscriptionForm({
            'level': 'v1-org-5',
            'last_4_card_digits': '0000',
            'stripe_token': 'GARYBUSEY',
            'business_vat_id': 'business-vat-id',
        },
            customer=self.user,
        )
        self.assertTrue(subscription_form.is_valid())
        subscription = subscription_form.save()

        self.assertEqual(subscription.level, 'v1-org-5')
        self.assertEqual(subscription.stripe_id, 'cus_12345')
        self.assertEqual(subscription.business_vat_id, 'business-vat-id')
        self.assertIsNotNone(self.user.gold)
        self.assertEqual(self.user.gold.first().level, 'v1-org-5')

        self.mocks['request'].request.assert_has_calls([
            mock.call('post',
                      '/v1/customers',
                      {'description': mock.ANY, 'email': mock.ANY, 'business_vat_id': 'business-vat-id'},
                      mock.ANY),
            mock.call('get',
                      '/v1/customers/cus_12345/subscriptions',
                      mock.ANY,
                      mock.ANY),
            mock.call('post',
                      '/v1/customers/cus_12345/subscriptions',
                      {'source': mock.ANY, 'plan': 'v1-org-5'},
                      mock.ANY),
        ])

    def test_add_subscription_update_user(self):
        """Valid subscription form"""
        subscription_list = {
            'object': 'list',
            'data': [],
            'has_more': False,
            'total_count': 1,
            'url': '/v1/customers/cus_12345/subscriptions',
        }
        customer_obj = {
            'id': 'cus_12345',
            'description': self.user.get_full_name(),
            'email': self.user.email,
            'subscriptions': subscription_list
        }
        subscription_obj = {
            'id': 'sub_12345',
            'object': 'subscription',
            'customer': 'cus_12345',
            'plan': {
                'id': 'v1-org-5',
                'object': 'plan',
                'amount': 1000,
                'currency': 'usd',
                'name': 'Test',
            }
        }
        self.mock_request([
            (customer_obj, ''),
            (customer_obj, ''),
            (subscription_list, ''),
            (subscription_obj, ''),
        ])

        # Create user and update the current gold subscription
        golduser = fixture.get(GoldUser, user=self.user, stripe_id='cus_12345')
        subscription_form = GoldSubscriptionForm(
            {'level': 'v1-org-5',
             'last_4_card_digits': '0000',
             'stripe_token': 'GARYBUSEY'},
            customer=self.user,
            instance=golduser
        )
        self.assertTrue(subscription_form.is_valid())
        subscription = subscription_form.save()

        self.assertEqual(subscription.level, 'v1-org-5')
        self.assertEqual(subscription.stripe_id, 'cus_12345')
        self.assertIsNotNone(self.user.gold)
        self.assertEqual(self.user.gold.first().level, 'v1-org-5')

        self.mocks['request'].request.assert_has_calls([
            mock.call('get',
                      '/v1/customers/cus_12345',
                      {},
                      mock.ANY),
            mock.call('post',
                      '/v1/customers/cus_12345',
                      {'description': mock.ANY, 'email': mock.ANY},
                      mock.ANY),
            mock.call('get',
                      '/v1/customers/cus_12345/subscriptions',
                      mock.ANY,
                      mock.ANY),
            mock.call('post',
                      '/v1/customers/cus_12345/subscriptions',
                      {'source': mock.ANY, 'plan': 'v1-org-5'},
                      mock.ANY),
        ])

    def test_update_subscription_plan(self):
        """Update subcription plan"""
        subscription_obj = {
            'id': 'sub_12345',
            'object': 'subscription',
            'customer': 'cus_12345',
            'plan': {
                'id': 'v1-org-5',
                'object': 'plan',
                'amount': 1000,
                'currency': 'usd',
                'name': 'Test',
            }
        }
        subscription_list = {
            'object': 'list',
            'data': [subscription_obj],
            'has_more': False,
            'total_count': 1,
            'url': '/v1/customers/cus_12345/subscriptions',
        }
        customer_obj = {
            'id': 'cus_12345',
            'description': self.user.get_full_name(),
            'email': self.user.email,
            'subscriptions': subscription_list
        }
        self.mock_request([
            (customer_obj, ''),
            (subscription_list, ''),
            (subscription_obj, ''),
        ])
        subscription_form = GoldSubscriptionForm(
            {'level': 'v1-org-5',
             'last_4_card_digits': '0000',
             'stripe_token': 'GARYBUSEY'},
            customer=self.user
        )
        self.assertTrue(subscription_form.is_valid())
        subscription = subscription_form.save()

        self.assertEqual(subscription.level, 'v1-org-5')
        self.assertIsNotNone(self.user.gold)
        self.assertEqual(self.user.gold.first().level, 'v1-org-5')

        self.mocks['request'].request.assert_has_calls([
            mock.call('post',
                      '/v1/customers',
                      {'description': mock.ANY, 'email': mock.ANY},
                      mock.ANY),
            mock.call('get',
                      '/v1/customers/cus_12345/subscriptions',
                      mock.ANY,
                      mock.ANY),
            mock.call('post',
                      '/v1/customers/cus_12345/subscriptions/sub_12345',
                      {'source': mock.ANY, 'plan': 'v1-org-5'},
                      mock.ANY),
        ])
