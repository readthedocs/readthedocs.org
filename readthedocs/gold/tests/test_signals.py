from __future__ import absolute_import
import mock
import django_dynamic_fixture as fixture
from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete

from readthedocs.projects.models import Project

from ..models import GoldUser
from ..signals import delete_customer


class GoldSignalTests(TestCase):

    def setUp(self):
        self.user = fixture.get(User)

        # Mocking
        self.patches = {}
        self.mocks = {}
        self.patches['requestor'] = mock.patch('stripe.api_requestor.APIRequestor')

        for patch in self.patches:
            self.mocks[patch] = self.patches[patch].start()

        self.mocks['request'] = self.mocks['requestor'].return_value

    def mock_request(self, resp=None):
        if resp is None:
            resp = ({}, '')
        self.mocks['request'].request = mock.Mock(side_effect=resp)

    def test_delete_subscription(self):
        subscription = fixture.get(GoldUser, user=self.user, stripe_id='cus_123')
        self.assertIsNotNone(subscription)
        self.mock_request([
            ({'id': 'cus_123', 'object': 'customer'}, ''),
            ({'deleted': True, 'customer': 'cus_123'}, ''),
        ])

        subscription.delete()

        self.mocks['request'].request.assert_has_calls([
            mock.call('get', '/v1/customers/cus_123', {}, mock.ANY),
            mock.call('delete', '/v1/customers/cus_123', {}, mock.ANY),
        ])
