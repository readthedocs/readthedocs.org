from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog


class TestSignals(TestCase):
    def setUp(self):
        self.user = get(
            User,
            username="test",
        )
        self.user.set_password("password")
        self.user.save()

    def test_log_logged_in(self):
        self.assertEqual(AuditLog.objects.all().count(), 0)
        self.assertTrue(self.client.login(username="test", password="password"))
        self.assertEqual(AuditLog.objects.all().count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, AuditLog.AUTHN)

    def test_log_logged_out(self):
        self.assertEqual(AuditLog.objects.all().count(), 0)
        self.assertTrue(self.client.login(username="test", password="password"))
        self.client.logout()
        self.assertEqual(AuditLog.objects.all().count(), 2)
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, AuditLog.LOGOUT)

    def test_log_login_failed(self):
        self.assertEqual(AuditLog.objects.all().count(), 0)
        self.assertFalse(self.client.login(username="test", password="incorrect"))
        self.assertEqual(AuditLog.objects.all().count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, AuditLog.AUTHN_FAILURE)
