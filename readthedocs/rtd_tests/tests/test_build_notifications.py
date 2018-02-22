# -*- coding: utf-8 -*-
"""Notifications sent after build is completed."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import django_dynamic_fixture as fixture
from django.core import mail
from django.test import TestCase
from mock import patch

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project, EmailHook, WebHook
from readthedocs.projects.tasks import send_notifications


class BuildNotificationsTests(TestCase):
    def setUp(self):
        self.project = fixture.get(Project)
        self.version = fixture.get(Version, project=self.project)
        self.build = fixture.get(Build, version=self.version)

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
