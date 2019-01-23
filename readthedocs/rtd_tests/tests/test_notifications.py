# -*- coding: utf-8 -*-
"""Notification tests."""


import django_dynamic_fixture as fixture
import mock
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from messages_extends.models import Message as PersistentMessage
from allauth.account.models import EmailAddress

from readthedocs.builds.models import Build
from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.backends import EmailBackend, SiteBackend
from readthedocs.notifications.constants import (
    ERROR,
    INFO_NON_PERSISTENT,
    WARNING_NON_PERSISTENT,
)
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import (
    DeprecatedBuildWebhookNotification,
    DeprecatedGitHubWebhookNotification,
)


@override_settings(
    NOTIFICATION_BACKENDS=[
        'readthedocs.notifications.backends.EmailBackend',
        'readthedocs.notifications.backends.SiteBackend',
    ],
    PRODUCTION_DOMAIN='readthedocs.org',
)
@mock.patch('readthedocs.notifications.notification.render_to_string')
@mock.patch.object(Notification, 'send')
class NotificationTests(TestCase):

    def test_notification_custom(self, send, render_to_string):
        render_to_string.return_value = 'Test'

        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        req = mock.MagicMock()
        notify = TestNotification(context_object=build, request=req)

        self.assertEqual(
            notify.get_template_names('email'),
            ['builds/notifications/foo_email.html'],
        )
        self.assertEqual(
            notify.get_template_names('site'),
            ['builds/notifications/foo_site.html'],
        )
        self.assertEqual(
            notify.get_subject(),
            'This is {}'.format(build.id),
        )
        self.assertEqual(
            notify.get_context_data(),
            {
                'foo': build,
                'production_uri': 'https://readthedocs.org',
                'request': req,
            },
        )

        notify.render('site')
        render_to_string.assert_has_calls([
            mock.call(
                context=mock.ANY,
                template_name=['builds/notifications/foo_site.html'],
            ),
        ])


@mock.patch('readthedocs.notifications.notification.render_to_string')
class NotificationBackendTests(TestCase):

    @mock.patch('readthedocs.notifications.backends.send_email')
    def test_email_backend(self, send_email, render_to_string):
        render_to_string.return_value = 'Test'

        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'
            level = ERROR

        build = fixture.get(Build)
        req = mock.MagicMock()
        user = fixture.get(User)
        notify = TestNotification(context_object=build, request=req, user=user)
        backend = EmailBackend(request=req)
        backend.send(notify)

        self.assertEqual(render_to_string.call_count, 1)
        send_email.assert_has_calls([
            mock.call(
                request=mock.ANY,
                template='core/email/common.txt',
                context={'content': 'Test'},
                subject='This is {}'.format(build.id),
                template_html='core/email/common.html',
                recipient=user.email,
            ),
        ])

    def test_message_backend(self, render_to_string):
        render_to_string.return_value = 'Test'

        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        user = fixture.get(User)
        req = mock.MagicMock()
        notify = TestNotification(context_object=build, request=req, user=user)
        backend = SiteBackend(request=req)
        backend.send(notify)

        self.assertEqual(render_to_string.call_count, 1)
        self.assertEqual(PersistentMessage.objects.count(), 1)

        message = PersistentMessage.objects.first()
        self.assertEqual(message.user, user)

    def test_message_anonymous_user(self, render_to_string):
        """Anonymous user still throwns exception on persistent messages."""
        render_to_string.return_value = 'Test'

        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        user = AnonymousUser()
        req = mock.MagicMock()
        notify = TestNotification(context_object=build, request=req, user=user)
        backend = SiteBackend(request=req)

        self.assertEqual(PersistentMessage.objects.count(), 0)

        # We should never be adding persistent messages for anonymous users.
        # Make sure message_extends sitll throws an exception here
        with self.assertRaises(NotImplementedError):
            backend.send(notify)

        self.assertEqual(render_to_string.call_count, 1)
        self.assertEqual(PersistentMessage.objects.count(), 0)

    @mock.patch('readthedocs.notifications.backends.send_email')
    def test_non_persistent_message(self, send_email, render_to_string):
        render_to_string.return_value = 'Test'

        class TestNotification(SiteNotification):
            name = 'foo'
            success_message = 'Test success message'
            success_level = INFO_NON_PERSISTENT

        user = fixture.get(User)
        # Setting the primary and verified email address of the user
        email = fixture.get(EmailAddress, user=user, primary=True, verified=True)

        n = TestNotification(user, True)
        backend = SiteBackend(request=None)

        self.assertEqual(PersistentMessage.objects.count(), 0)
        backend.send(n)
        # No email is sent for non persistent messages
        send_email.assert_not_called()
        self.assertEqual(PersistentMessage.objects.count(), 1)
        self.assertEqual(PersistentMessage.objects.filter(read=False).count(), 1)

        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'Test success message')
        self.assertEqual(PersistentMessage.objects.count(), 1)
        self.assertEqual(PersistentMessage.objects.filter(read=True).count(), 1)

        response = self.client.get('/dashboard/')
        self.assertNotContains(response, 'Test success message')


@override_settings(PRODUCTION_DOMAIN='readthedocs.org')
class SiteNotificationTests(TestCase):

    class TestSiteNotification(SiteNotification):
        name = 'foo'
        success_message = 'simple success message'
        failure_message = {
            1: 'simple failure message',
            2: '{{ object.name }} object name',
            'three': '{{ object.name }} and {{ other.name }} render',
        }
        success_level = INFO_NON_PERSISTENT
        failure_level = WARNING_NON_PERSISTENT

    def setUp(self):
        self.user = fixture.get(User)
        self.context = {'other': {'name': 'other name'}}
        self.n = self.TestSiteNotification(
            self.user,
            True,
            context_object={'name': 'object name'},
            extra_context=self.context,
        )

    def test_context_data(self):
        context = {
            'object': {'name': 'object name'},
            'request': None,
            'production_uri': 'https://readthedocs.org',
            'other': {'name': 'other name'},
        }
        self.assertEqual(self.n.get_context_data(), context)

    def test_message_level(self):
        self.n.success = True
        self.assertEqual(self.n.get_message_level(), INFO_NON_PERSISTENT)

        self.n.success = False
        self.assertEqual(self.n.get_message_level(), WARNING_NON_PERSISTENT)

    def test_message(self):
        self.n.reason = 1
        self.assertEqual(self.n.get_message(True), 'simple success message')
        self.n.reason = 'three'
        self.assertEqual(self.n.get_message(True), 'simple success message')

        self.n.reason = 1
        self.assertEqual(self.n.get_message(False), 'simple failure message')
        self.n.reason = 2
        self.assertEqual(self.n.get_message(False), 'object name object name')
        self.n.reason = 'three'
        self.assertEqual(self.n.get_message(False), 'object name and other name render')

        # Invalid reason
        self.n.reason = None
        with mock.patch('readthedocs.notifications.notification.log') as mock_log:
            self.assertEqual(self.n.get_message(False), '')
            mock_log.error.assert_called_once()


class DeprecatedWebhookEndpointNotificationTests(TestCase):

    def setUp(self):
        PersistentMessage.objects.all().delete()

        self.user = fixture.get(User)
        self.project = fixture.get(Project, users=[self.user])
        self.request = HttpRequest()

        self.notification = DeprecatedBuildWebhookNotification(
            self.project,
            self.request,
            self.user,
        )

    @mock.patch('readthedocs.notifications.backends.send_email')
    def test_dedupliation(self, send_email):
        user = fixture.get(User)
        project = fixture.get(Project, main_language_project=None)
        project.users.add(user)
        project.refresh_from_db()
        self.assertEqual(project.users.count(), 1)

        self.assertEqual(PersistentMessage.objects.filter(user=user).count(), 0)
        DeprecatedGitHubWebhookNotification.notify_project_users([project])

        # Site and email notification will go out, site message doesn't have
        # any reason to deduplicate yet
        self.assertEqual(PersistentMessage.objects.filter(user=user).count(), 1)
        self.assertTrue(send_email.called)
        send_email.reset_mock()
        self.assertFalse(send_email.called)

        # Expect the site message to deduplicate, the email won't
        DeprecatedGitHubWebhookNotification.notify_project_users([project])
        self.assertEqual(PersistentMessage.objects.filter(user=user).count(), 1)
        self.assertTrue(send_email.called)
        send_email.reset_mock()
