from unittest import mock

import requests_mock
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.support.views import FrontWebhookBase


@override_settings(
    ADMIN_URL='https://readthedocs.org/admin',
    FRONT_API_SECRET='1234',
    FRONT_TOKEN='1234',
)
class TestFrontWebhook(TestCase):

    def setUp(self):
        self.user = get(User, email='test@example.com', username='test')
        self.url = reverse('front_webhook')

    def test_invalid_payload(self):
        resp = self.client.post(
            self.url,
            data={'foo': 'bar'},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['detail'], 'Invalid payload')

    @mock.patch.object(FrontWebhookBase, '_is_payload_valid')
    def test_invalid_event(self, is_payload_valid):
        is_payload_valid.return_value = True
        resp = self.client.post(
            self.url,
            data={'type': 'outbound'},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Skipping outbound event')

    @requests_mock.Mocker(kw='mock_request')
    @mock.patch.object(FrontWebhookBase, '_is_payload_valid')
    def test_inbound_event(self, is_payload_valid, mock_request):
        is_payload_valid.return_value = True
        self._mock_request(mock_request)
        resp = self.client.post(
            self.url,
            data={
                'type': 'inbound',
                'conversation': {'id': 'cnv_123'}
            },
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'User updated test@example.com')
        last_request = mock_request.last_request
        self.assertEqual(last_request.method, 'PATCH')
        # Existing custom fields are left unchanged.
        custom_fields = last_request.json()['custom_fields']
        for field in ['com:dont-change', 'org:dont-change', 'ads:dont-change']:
            self.assertEqual(custom_fields[field], 'Do not change this')

    @requests_mock.Mocker(kw='mock_request')
    @mock.patch.object(FrontWebhookBase, '_is_payload_valid')
    def test_inbound_event_unknow_email(self, is_payload_valid, mock_request):
        self.user.email = 'unknown@example.com'
        self.user.save()
        is_payload_valid.return_value = True
        self._mock_request(mock_request)
        resp = self.client.post(
            self.url,
            data={
                'type': 'inbound',
                'conversation': {'id': 'cnv_123'}
            },
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data['detail'],
            'User with email test@example.com not found in our database',
        )

    def _mock_request(self, mock_request):
        mock_request.get(
            'https://api2.frontapp.com/conversations/cnv_123',
            json={
                'recipient': {
                    'handle': 'test@example.com',
                },
            },
        )
        mock_request.get(
            'https://api2.frontapp.com/contacts/alt:email:test@example.com',
            json={
                'custom_fields': {
                    'org:dont-change': 'Do not change this',
                    'com:dont-change': 'Do not change this',
                    'ads:dont-change': 'Do not change this',
                },
            },
        )
        mock_request.patch('https://api2.frontapp.com/contacts/alt:email:test@example.com')
