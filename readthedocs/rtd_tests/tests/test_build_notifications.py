"""Notifications sent after build is completed."""

import json

import django_dynamic_fixture as fixture
from django.core import mail
from django.test import TestCase
from unittest.mock import patch

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.projects.forms import WebHookForm
from readthedocs.projects.models import EmailHook, Project, WebHook
from readthedocs.projects.tasks import send_notifications


class BuildNotificationsTests(TestCase):
    def setUp(self):
        self.project = fixture.get(Project)
        self.version = fixture.get(Version, project=self.project)
        self.build = fixture.get(Build, version=self.version)

    @patch('readthedocs.builds.managers.log')
    def test_send_notification_none_if_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        send_notifications(version_pk=345343, build_pk=None)
        mock_logger.warning.assert_called_with(
            'Version not found for given kwargs. %s',
            {'pk': 345343},
        )


    def test_send_notification_none(self):
        send_notifications(self.version.pk, self.build.pk)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_webhook_notification(self):
        fixture.get(WebHook, project=self.project)
        with patch('readthedocs.projects.tasks.requests.post') as mock:
            mock.return_value = None
            send_notifications(self.version.pk, self.build.pk)
            mock.assert_called_once()

        self.assertEqual(len(mail.outbox), 0)

    def test_dont_send_webhook_notifications_for_external_versions(self):
        fixture.get(WebHook, project=self.project)
        self.version.type = EXTERNAL
        self.version.save()

        with patch('readthedocs.projects.tasks.requests.post') as mock:
            mock.return_value = None
            send_notifications(self.version.pk, self.build.pk)
            mock.assert_not_called()

        self.assertEqual(len(mail.outbox), 0)

    def test_send_webhook_notification_has_content_type_header(self):
        hook = fixture.get(WebHook, project=self.project)
        data = json.dumps({
            'name': self.project.name,
            'slug': self.project.slug,
            'build': {
                'id': self.build.id,
                'commit': self.build.commit,
                'state': self.build.state,
                'success': self.build.success,
                'date': self.build.date.strftime('%Y-%m-%d %H:%M:%S'),
            },
        })
        with patch('readthedocs.projects.tasks.requests.post') as mock:
            mock.return_value = None
            send_notifications(self.version.pk, self.build.pk)
            mock.assert_called_once_with(
                hook.url,
                data=data,
                headers={'content-type': 'application/json'}
            )

    def test_send_email_notification(self):
        fixture.get(EmailHook, project=self.project)
        send_notifications(self.version.pk, self.build.pk, email=True)
        self.assertEqual(len(mail.outbox), 1)

    def test_dont_send_email_notifications_for_external_versions(self):
        fixture.get(EmailHook, project=self.project)
        self.version.type = EXTERNAL
        self.version.save()

        send_notifications(self.version.pk, self.build.pk, email=True)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_email_and_webhook__notification(self):
        fixture.get(EmailHook, project=self.project)
        fixture.get(WebHook, project=self.project)
        with patch('readthedocs.projects.tasks.requests.post') as mock:
            mock.return_value = None
            send_notifications(self.version.pk, self.build.pk, email=True)
            mock.assert_called_once()
        self.assertEqual(len(mail.outbox), 1)


class TestForms(TestCase):

    def setUp(self):
        self.project = fixture.get(Project)
        self.version = fixture.get(Version, project=self.project)
        self.build = fixture.get(Build, version=self.version)

    def test_webhook_form_url_length(self):
        form = WebHookForm(
            {
                'url': 'https://foobar.com',
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid())

        form = WebHookForm(
            {
                'url': 'foo' * 500,
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                'url':
                   [
                       'Enter a valid URL.',
                       'Ensure this value has at most 600 characters (it has 1507).',
                   ],
                },
        )
