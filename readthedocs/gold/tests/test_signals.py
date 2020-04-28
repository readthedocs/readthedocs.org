# -*- coding: utf-8 -*-
import django_dynamic_fixture as fixture
from unittest import mock
from django.contrib.auth.models import User
from django.test import TestCase

from ..models import GoldUser


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
