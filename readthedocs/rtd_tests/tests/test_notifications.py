"""Notification tests"""

from __future__ import absolute_import
import mock
import django_dynamic_fixture as fixture
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User, AnonymousUser
from messages_extends.models import Message as PersistentMessage

from readthedocs.notifications import Notification
from readthedocs.notifications.backends import EmailBackend, SiteBackend
from readthedocs.notifications.constants import ERROR
from readthedocs.builds.models import Build


@override_settings(
    NOTIFICATION_BACKENDS=[
        'readthedocs.notifications.backends.EmailBackend',
        'readthedocs.notifications.backends.SiteBackend'
    ]
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

        self.assertEqual(notify.get_template_names('email'),
                         ['builds/notifications/foo_email.html'])
        self.assertEqual(notify.get_template_names('site'),
                         ['builds/notifications/foo_site.html'])
        self.assertEqual(notify.get_subject(),
                         'This is {0}'.format(build.id))
        self.assertEqual(notify.get_context_data(),
                         {'foo': build,
                          'production_uri': 'https://readthedocs.org',
                          'request': req})

        notify.render('site')
        render_to_string.assert_has_calls([
            mock.call(context=mock.ANY,
                      template_name=['builds/notifications/foo_site.html'])
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
                subject=u'This is 1',
                template_html='core/email/common.html',
                recipient=user.email,
            )
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
        """Anonymous user still throwns exception on persistent messages"""
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
