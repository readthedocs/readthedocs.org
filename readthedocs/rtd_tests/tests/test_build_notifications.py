"""Notifications sent after build is completed."""
import hashlib
import hmac
import json
from unittest import mock

import requests_mock
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.builds.tasks import send_build_notifications
from readthedocs.projects.forms import WebHookForm
from readthedocs.projects.models import EmailHook, Project, WebHook, WebHookEvent


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    PUBLIC_DOMAIN="readthedocs.io",
)
class BuildNotificationsTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="test", language="en")
        self.version = get(Version, project=self.project, slug="1.0")
        self.build = get(Build, version=self.version, commit="abc1234567890")

    @mock.patch("readthedocs.builds.managers.log")
    def test_send_notification_none_if_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        send_build_notifications(
            version_pk=345343,
            build_pk=None,
            event=WebHookEvent.BUILD_FAILED,
        )
        mock_logger.warning.assert_called_with(
            "Version not found for given kwargs.",
            kwargs={"pk": 345343},
        )

    def test_send_notification_none(self):
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(len(mail.outbox), 0)

    @requests_mock.Mocker(kw="mock_request")
    def test_send_webhook_notification(self, mock_request):
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        )
        self.assertEqual(webhook.exchanges.all().count(), 0)
        mock_request.post(webhook.url)
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(webhook.exchanges.all().count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_dont_send_webhook_notifications_for_external_versions(self):
        webhook = get(WebHook, url="https://example.com/webhook/", project=self.project)
        self.version.type = EXTERNAL
        self.version.save()
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(webhook.exchanges.all().count(), 0)

    def test_webhook_notification_has_content_type_header(self):
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        )
        data = json.dumps(
            {
                "name": self.project.name,
                "slug": self.project.slug,
                "build": {
                    "id": self.build.id,
                    "commit": self.build.commit,
                    "state": self.build.state,
                    "success": self.build.success,
                    "date": self.build.date.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        )
        with mock.patch("readthedocs.builds.tasks.requests.post") as post:
            post.return_value = None
            send_build_notifications(
                version_pk=self.version.pk,
                build_pk=self.build.pk,
                event=WebHookEvent.BUILD_FAILED,
            )
            post.assert_called_once_with(
                webhook.url,
                data=data,
                headers={
                    "content-type": "application/json",
                    "X-Hub-Signature": mock.ANY,
                    "User-Agent": mock.ANY,
                    "X-RTD-Event": mock.ANY,
                },
                timeout=mock.ANY,
            )

    @requests_mock.Mocker(kw="mock_request")
    def test_send_webhook_custom_on_given_event(self, mock_request):
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[
                WebHookEvent.objects.get(name=WebHookEvent.BUILD_TRIGGERED),
                WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED),
            ],
            payload="{}",
        )
        mock_request.post(webhook.url)
        for event, _ in WebHookEvent.EVENTS:
            send_build_notifications(
                version_pk=self.version.pk,
                build_pk=self.build.pk,
                event=event,
            )
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(webhook.exchanges.all().count(), 2)

    @requests_mock.Mocker(kw="mock_request")
    def test_send_webhook_custom_payload(self, mock_request):
        self.build.date = timezone.datetime(
            year=2021,
            month=3,
            day=15,
            hour=15,
            minute=30,
            second=4,
        )
        self.build.save()
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED)],
            payload=json.dumps(
                {
                    "message": "Event {{ event }} triggered for {{ version.slug }}",
                    "extra-data": {
                        "build_id": "{{build.id}}",
                        "build_commit": "{{build.commit}}",
                        "build_url": "{{ build.url }}",
                        "build_docsurl": "{{ build.docs_url }}",
                        "build_start_date": "{{ build.start_date }}",
                        "organization_slug": "{{ organization.slug }}",
                        "organization_name": "{{ organization.name }}",
                        "project_slug": "{{ project.slug }}",
                        "project_name": "{{ project.name }}",
                        "project_url": "{{ project.url }}",
                        "version_slug": "{{ version.slug }}",
                        "version_name": "{{ version.name }}",
                        "invalid_substitution": "{{ invalid.substitution }}",
                    },
                }
            ),
        )
        post = mock_request.post(webhook.url)
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertTrue(post.called_once)
        request = post.request_history[0]
        self.assertEqual(
            request.json(),
            {
                "message": f"Event build:failed triggered for {self.version.slug}",
                "extra-data": {
                    "build_id": str(self.build.pk),
                    "build_commit": self.build.commit,
                    "build_url": f"https://readthedocs.org{self.build.get_absolute_url()}",
                    "build_docsurl": "http://test.readthedocs.io/en/1.0/",
                    "build_start_date": "2021-03-15T15:30:04",
                    "organization_name": "",
                    "organization_slug": "",
                    "project_name": self.project.name,
                    "project_slug": self.project.slug,
                    "project_url": f"https://readthedocs.org{self.project.get_absolute_url()}",
                    "version_name": self.version.verbose_name,
                    "version_slug": self.version.slug,
                    "invalid_substitution": "{{ invalid.substitution }}",
                },
            },
        )
        self.assertEqual(webhook.exchanges.all().count(), 1)

    @requests_mock.Mocker(kw="mock_request")
    def test_webhook_headers(self, mock_request):
        secret = "1234"
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED)],
            payload='{"sign": "me"}',
            secret=secret,
        )
        post = mock_request.post(webhook.url)
        signature = hmac.new(
            key=secret.encode(),
            msg=webhook.payload.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertTrue(post.called_once)
        request = post.request_history[0]
        headers = request.headers
        self.assertTrue(headers["User-Agent"].startswith("Read-the-Docs/"))
        self.assertEqual(headers["X-Hub-Signature"], signature)
        self.assertEqual(headers["X-RTD-Event"], WebHookEvent.BUILD_FAILED)
        self.assertEqual(webhook.exchanges.all().count(), 1)

    @requests_mock.Mocker(kw="mock_request")
    def test_webhook_record_exchange(self, mock_request):
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED)],
            payload='{"request": "ok"}',
        )
        post = mock_request.post(
            webhook.url,
            json={"response": "ok"},
            headers={"X-Greeting": "Hi!"},
            status_code=201,
        )
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertTrue(post.called_once)
        self.assertEqual(webhook.exchanges.all().count(), 1)
        exchange = webhook.exchanges.all().first()
        self.assertTrue(
            exchange.request_headers["User-Agent"].startswith("Read-the-Docs/")
        )
        self.assertIn("X-Hub-Signature", exchange.request_headers)
        self.assertEqual(exchange.request_body, webhook.payload)
        self.assertEqual(exchange.response_headers, {"X-Greeting": "Hi!"})
        self.assertEqual(exchange.response_body, '{"response": "ok"}')
        self.assertEqual(exchange.status_code, 201)

    def test_send_email_notification_on_build_failure(self):
        get(EmailHook, project=self.project)
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_dont_send_email_notifications_for_external_versions(self):
        get(EmailHook, project=self.project)
        self.version.type = EXTERNAL
        self.version.save()

        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_dont_send_email_notifications_for_other_events(self):
        """Email notifications are only send for BUILD_FAILED events."""
        get(EmailHook, project=self.project)
        for event in [WebHookEvent.BUILD_PASSED, WebHookEvent.BUILD_TRIGGERED]:
            send_build_notifications(
                version_pk=self.version.pk,
                build_pk=self.build.pk,
                event=event,
            )
        self.assertEqual(len(mail.outbox), 0)

    @requests_mock.Mocker(kw="mock_request")
    def test_send_email_and_webhook_notification(self, mock_request):
        get(EmailHook, project=self.project)
        webhook = get(
            WebHook,
            url="https://example.com/webhook/",
            project=self.project,
            events=[WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
        )
        mock_request.post(webhook.url)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(webhook.exchanges.all().count(), 0)
        send_build_notifications(
            version_pk=self.version.pk,
            build_pk=self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(webhook.exchanges.all().count(), 1)


class TestForms(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)
        self.build = get(Build, version=self.version)

    def test_webhook_form_url_length(self):
        form = WebHookForm(
            {
                "url": "https://foobar.com",
                "payload": "{}",
                "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid())

        form = WebHookForm(
            {
                "url": "foo" * 500,
                "payload": "{}",
                "events": [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "url": [
                    "Enter a valid URL.",
                    "Ensure this value has at most 600 characters (it has 1507).",
                ],
            },
        )
