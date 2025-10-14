"""Notification tests."""


from unittest import mock

import django_dynamic_fixture as fixture
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.models import Build
from readthedocs.notifications.email import EmailNotification


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    SUPPORT_EMAIL="support@readthedocs.org",
)
@mock.patch("readthedocs.notifications.email.render_to_string")
@mock.patch.object(EmailNotification, "send")
class NotificationTests(TestCase):
    def test_notification_custom(self, send, render_to_string):
        render_to_string.return_value = "Test"

        class TestNotification(EmailNotification):
            name = "foo"
            subject = "This is {{ foo.id }}"
            context_object_name = "foo"

        user = fixture.get(User)
        build = fixture.get(Build)
        notify = TestNotification(context_object=build, user=user)

        self.assertEqual(
            notify.get_template_names("html"),
            ["builds/notifications/foo_email.html"],
        )
        self.assertEqual(
            notify.get_template_names("txt"),
            ["builds/notifications/foo_email.txt"],
        )
        self.assertEqual(
            notify.get_subject(),
            "This is {}".format(build.id),
        )
        self.assertEqual(
            notify.get_context_data(),
            {
                "foo": build,
                "production_uri": "https://readthedocs.org",
                # readthedocs_processor context
                "ADMIN_URL": mock.ANY,
                "DASHBOARD_ANALYTICS_CODE": mock.ANY,
                "DO_NOT_TRACK_ENABLED": mock.ANY,
                "GLOBAL_ANALYTICS_CODE": mock.ANY,
                "PRODUCTION_DOMAIN": "readthedocs.org",
                "PUBLIC_DOMAIN": mock.ANY,
                "PUBLIC_API_URL": mock.ANY,
                "SITE_ROOT": mock.ANY,
                "SUPPORT_EMAIL": "support@readthedocs.org",
                "TEMPLATE_ROOT": mock.ANY,
                "USE_PROMOS": mock.ANY,
                "USE_ORGANIZATIONS": mock.ANY,
                "GITHUB_APP_NAME": mock.ANY,
            },
        )

        notify.render("html")
        render_to_string.assert_has_calls(
            [
                mock.call(
                    context=mock.ANY,
                    template_name=["builds/notifications/foo_email.html"],
                ),
            ]
        )


class NotificationBackendTests(TestCase):
    @mock.patch("readthedocs.notifications.email.send_email")
    def test_email_backend(self, send_email):
        class TestNotification(EmailNotification):
            name = "foo"
            subject = "This is {{ foo.id }}"
            context_object_name = "foo"

        build = fixture.get(Build)
        user = fixture.get(User)
        notify = TestNotification(context_object=build, user=user)
        notify.send()

        send_email.assert_has_calls(
            [
                mock.call(
                    template=["builds/notifications/foo_email.txt"],
                    context=notify.get_context_data(),
                    subject="This is {}".format(build.id),
                    template_html=["builds/notifications/foo_email.html"],
                    recipient=user.email,
                ),
            ]
        )
