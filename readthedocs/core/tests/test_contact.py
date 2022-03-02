from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.core.utils.contact import contact_users
from readthedocs.notifications.backends import SiteBackend

User = get_user_model()

class TestContactUsers(TestCase):

    def setUp(self):
        self.user = get(User, username='test', email='one@test.com')
        self.user_two = get(User, username='test2', email='two@test.com')
        self.user_three = get(User, username='test3', email='three@test.com')
    
    @mock.patch('readthedocs.core.utils.contact.send_mail')
    @mock.patch.object(SiteBackend, 'send')
    def test_contact_users_dryrun(self, send_notification, send_mail):
        self.assertEqual(User.objects.all().count(), 3)
        resp = contact_users(
            users=User.objects.all(),
            email_subject='Subject',
            email_content='Content',
            notification_content='Notification',
            dryrun=True,
        )
        self.assertEqual(
            resp,
            {
                'email': {
                    'sent': {'one@test.com', 'two@test.com', 'three@test.com'},
                    'failed': set(),
                },
                'notification': {
                    'sent': {
                        self.user.username,
                        self.user_two.username,
                        self.user_three.username,
                    },
                    'failed': set(),
                }
            }
        )

        self.assertEqual(send_notification.call_count, 0)
        self.assertEqual(send_mail.call_count, 0)

    @mock.patch('readthedocs.core.utils.contact.send_mail')
    @mock.patch.object(SiteBackend, 'send')
    def test_contact_users_not_dryrun(self, send_notification, send_mail):
        self.assertEqual(User.objects.all().count(), 3)
        resp = contact_users(
            users=User.objects.all(),
            email_subject='Subject',
            email_content='Content',
            notification_content='Notification',
            dryrun=False,
        )
        self.assertEqual(
            resp,
            {
                'email': {
                    'sent': {'one@test.com', 'two@test.com', 'three@test.com'},
                    'failed': set(),
                },
                'notification': {
                    'sent': {
                        self.user.username,
                        self.user_two.username,
                        self.user_three.username,
                    },
                    'failed': set(),
                }
            }
        )

        self.assertEqual(send_notification.call_count, 3)
        self.assertEqual(send_mail.call_count, 3)
