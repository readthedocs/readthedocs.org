# -*- coding: utf-8 -*-
"""Notifications sent after build is completed."""

import django_dynamic_fixture as fixture
from django.core import mail
from django.test import TestCase
from mock import patch

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
        mock_logger.warning.assert_called_with("Version not found for given kwargs. {'pk': 345343}")


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

    def test_send_email_notification(self):
        fixture.get(EmailHook, project=self.project)
        send_notifications(self.version.pk, self.build.pk)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_and_webhook__notification(self):
        fixture.get(EmailHook, project=self.project)
        fixture.get(WebHook, project=self.project)
        with patch('readthedocs.projects.tasks.requests.post') as mock:
            mock.return_value = None
            send_notifications(self.version.pk, self.build.pk)
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
