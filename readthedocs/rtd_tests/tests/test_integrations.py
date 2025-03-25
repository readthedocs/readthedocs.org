import django_dynamic_fixture as fixture
from django.test import TestCase
from rest_framework.test import APIClient

from readthedocs.api.v2.views.integrations import GITHUB_SIGNATURE_HEADER
from readthedocs.integrations.models import GitHubWebhook, HttpExchange, Integration
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.tests.test_api import get_signature


class HttpExchangeTests(TestCase):

    """
    Test HttpExchange model by using existing views.

    This doesn't mock out a req/resp cycle, as manually creating these outside
    views misses a number of attributes on the request object.
    """

    def test_exchange_json_request_body(self):
        client = APIClient()
        client.login(username="super", password="test")
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(
            Integration,
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data="",
        )
        payload = {"ref": "refs/heads/exchange_json"}
        signature = get_signature(integration, payload)
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(project.slug),
            payload,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: signature,
            },
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_body,
            '{"ref": "refs/heads/exchange_json"}',
        )
        self.assertEqual(
            exchange.request_headers,
            {
                "Content-Type": "application/json",
                "Cookie": "",
                "X-Hub-Signature-256": signature,
            },
        )
        self.assertEqual(
            exchange.response_body,
            (
                '{{"build_triggered": false, "project": "{0}", "versions": []}}'.format(
                    project.slug
                )
            ),
        )
        self.assertEqual(
            exchange.response_headers,
            {
                "Allow": "POST, OPTIONS",
                "Content-Type": "text/html; charset=utf-8",
            },
        )

    def test_exchange_form_request_body(self):
        client = APIClient()
        client.login(username="super", password="test")
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(
            Integration,
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data="",
            secret=None,
        )
        payload = "payload=%7B%22ref%22:%20%22refs/heads/exchange_form%22%7D"
        signature = get_signature(integration, payload)
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(project.slug),
            payload,
            content_type="application/x-www-form-urlencoded",
            headers={
                GITHUB_SIGNATURE_HEADER: signature,
            },
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_body,
            '{"ref": "refs/heads/exchange_form"}',
        )
        self.assertEqual(
            exchange.request_headers,
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "",
                "X-Hub-Signature-256": signature,
            },
        )
        self.assertEqual(
            exchange.response_body,
            (
                '{{"build_triggered": false, "project": "{0}", "versions": []}}'.format(
                    project.slug
                )
            ),
        )
        self.assertEqual(
            exchange.response_headers,
            {
                "Allow": "POST, OPTIONS",
                "Content-Type": "text/html; charset=utf-8",
            },
        )

    def test_extraneous_exchanges_deleted_in_correct_order(self):
        client = APIClient()
        client.login(username="super", password="test")
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(
            Integration,
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data="",
        )

        self.assertEqual(
            HttpExchange.objects.filter(integrations=integration).count(),
            0,
        )

        for _ in range(10):
            resp = client.post(
                "/api/v2/webhook/github/{}/".format(project.slug),
                {"ref": "deleted"},
                format="json",
            )
        for _ in range(10):
            resp = client.post(
                "/api/v2/webhook/github/{}/".format(project.slug),
                {"ref": "preserved"},
                format="json",
            )

        self.assertEqual(
            HttpExchange.objects.filter(integrations=integration).count(),
            10,
        )
        self.assertEqual(
            HttpExchange.objects.filter(
                integrations=integration,
                request_body='{"ref": "preserved"}',
            ).count(),
            10,
        )

    def test_request_headers_are_removed(self):
        client = APIClient()
        client.login(username="super", password="test")
        project = fixture.get(Project, main_language_project=None)
        integration = fixture.get(
            Integration,
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data="",
        )
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(project.slug),
            {"ref": "exchange_json"},
            format="json",
            HTTP_X_FORWARDED_FOR="1.2.3.4",
            HTTP_X_REAL_IP="5.6.7.8",
            HTTP_X_FOO="bar",
        )
        exchange = HttpExchange.objects.get(integrations=integration)
        self.assertEqual(
            exchange.request_headers,
            {
                "Content-Type": "application/json",
                "Cookie": "",
                "X-Foo": "bar",
            },
        )


class IntegrationModelTests(TestCase):
    def test_subclass_is_replaced_on_get(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
        )
        integration = Integration.objects.get(pk=integration.pk)
        self.assertIsInstance(integration, GitHubWebhook)

    def test_subclass_is_replaced_on_subclass(self):
        project = fixture.get(Project, main_language_project=None)
        integration = Integration.objects.create(
            project=project,
            integration_type=Integration.GITHUB_WEBHOOK,
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
