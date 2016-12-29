"""Notification tests"""

import mock
import django_dynamic_fixture as fixture
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User

from readthedocs.notifications import Notification
from readthedocs.notifications.backends import EmailBackend, SiteBackend
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
        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        req = mock.MagicMock()
        notify = TestNotification(object=build, request=req)

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
        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        req = mock.MagicMock()
        notify = TestNotification(object=build, request=req)
        backend = EmailBackend(request=req)
        backend.send(notify)

        send_email.assert_has_calls([
            mock.call(level=21, request=req, message=mock.ANY, extra_tags='')
        ])

    @mock.patch('readthedocs.notifications.storages.FallbackUniqueStorage')
    def test_email_backend(self, storage_class, render_to_string):
        mock_storage = mock.Mock()
        storage_class.return_value = mock_storage

        class TestNotification(Notification):
            name = 'foo'
            subject = 'This is {{ foo.id }}'
            context_object_name = 'foo'

        build = fixture.get(Build)
        user = fixture.get(User)
        req = mock.MagicMock()
        notify = TestNotification(object=build, request=req, user=user)
        backend = SiteBackend(request=req)
        backend.send(notify)

        mock_storage.add.assert_has_calls([
            mock.call(level=21, message=mock.ANY, extra_tags='', user=user)
        ])
