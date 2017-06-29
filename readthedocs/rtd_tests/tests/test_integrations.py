from __future__ import absolute_import

from builtins import range
import django_dynamic_fixture as fixture
from django.test import TestCase, RequestFactory
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response

from readthedocs.integrations.models import (
    HttpExchange, Integration, GitHubWebhook
)
from readthedocs.projects.models import Project


class HttpExchangeTests(TestCase):

    """Test HttpExchange model by using existing views

    This doesn't mock out a req/resp cycle, as manually creating these outside
    views misses a number of attributes on the request object.
    """

    def test_exchange_json_request_body(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(Integration, project=project,
                                  integration_type=Integration.GITHUB_WEBHOOK,
                                  provider_data='')
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(project.slug),
            {'ref': 'exchange_json'},
            format='json'
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_body,
            '{"ref": "exchange_json"}'
        )
        self.assertEqual(
            exchange.request_headers,
            {u'Content-Type': u'application/json; charset=None',
             u'Cookie': u''}
        )
        self.assertEqual(
            exchange.response_body,
            ('{{"build_triggered": false, "project": "{0}", "versions": []}}'
             .format(project.slug)),
        )
        self.assertEqual(
            exchange.response_headers,
            {u'Allow': u'POST, OPTIONS',
             u'Content-Type': u'text/html; charset=utf-8'}
        )

    def test_exchange_form_request_body(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(Integration, project=project,
                                  integration_type=Integration.GITHUB_WEBHOOK,
                                  provider_data='')
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(project.slug),
            'payload=%7B%22ref%22%3A+%22exchange_form%22%7D',
            content_type='application/x-www-form-urlencoded',
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_body,
            '{"ref": "exchange_form"}'
        )
        self.assertEqual(
            exchange.request_headers,
            {u'Content-Type': u'application/x-www-form-urlencoded',
             u'Cookie': u''}
        )
        self.assertEqual(
            exchange.response_body,
            ('{{"build_triggered": false, "project": "{0}", "versions": []}}'
             .format(project.slug)),
        )
        self.assertEqual(
            exchange.response_headers,
            {u'Allow': u'POST, OPTIONS',
             u'Content-Type': u'text/html; charset=utf-8'}
        )

    def test_extraneous_exchanges_deleted_in_correct_order(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(Integration, project=project,
                                  integration_type=Integration.GITHUB_WEBHOOK,
                                  provider_data='')

        self.assertEqual(
            HttpExchange.objects.filter(integrations=integration).count(),
            0
        )

        for _ in range(10):
            resp = client.post(
                '/api/v2/webhook/github/{0}/'.format(project.slug),
                {'ref': 'deleted'},
                format='json'
            )
        for _ in range(10):
            resp = client.post(
                '/api/v2/webhook/github/{0}/'.format(project.slug),
                {'ref': 'preserved'},
                format='json'
            )

        self.assertEqual(
            HttpExchange.objects.filter(integrations=integration).count(),
            10
        )
        self.assertEqual(
            HttpExchange.objects.filter(
                integrations=integration,
                request_body='{"ref": "preserved"}',
            ).count(),
            10
        )

    def test_request_headers_are_removed(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(Integration, project=project,
                                  integration_type=Integration.GITHUB_WEBHOOK,
                                  provider_data='')
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(project.slug),
            {'ref': 'exchange_json'},
            format='json',
            HTTP_X_FORWARDED_FOR='1.2.3.4',
            HTTP_X_REAL_IP='5.6.7.8',
            HTTP_X_FOO='bar',
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_headers,
            {u'Content-Type': u'application/json; charset=None',
             u'Cookie': u'',
             u'X-Foo': u'bar'}
        )


class IntegrationModelTests(TestCase):

    def test_subclass_is_replaced_on_get(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK
        )
        integration = Integration.objects.get(pk=integration.pk)
        self.assertIsInstance(integration, GitHubWebhook)

    def test_subclass_is_replaced_on_subclass(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK
        )
        integration = Integration.objects.subclass(integration)
        self.assertIsInstance(integration, GitHubWebhook)

    def test_subclass_is_replaced_on_create(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            integration_type=Integration.GITHUB_WEBHOOK,
            project=project,
        )
        self.assertIsInstance(integration, GitHubWebhook)

    def test_generic_token(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            integration_type=Integration.API_WEBHOOK,
            project=project,
        )
        self.assertIsNotNone(integration.token)
