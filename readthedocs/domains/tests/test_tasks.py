from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.domains.tasks import email_pending_custom_domains
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.constants import (
    SSL_STATUS_INVALID,
    SSL_STATUS_PENDING,
    SSL_STATUS_VALID,
)
from readthedocs.projects.models import Domain, Project


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestTasks(TestCase):
    def setUp(self):
        self.user = get(User, email="user@example.com")
        self.another_user = get(User, email="anotheruser@example.com")
        self.project = get(Project, users=[self.user])
        self.another_project = get(Project, users=[self.user, self.another_user])

        self.domain = get(
            Domain,
            project=self.project,
            ssl_status=SSL_STATUS_VALID,
            domain="docs.domain.com",
        )
        self.domain_pending = get(
            Domain,
            project=self.project,
            ssl_status=SSL_STATUS_PENDING,
            domain="docs.domain2.com",
        )
        self.domain_invalid = get(
            Domain,
            project=self.another_project,
            ssl_status=SSL_STATUS_INVALID,
            domain="docs.domain3.com",
        )
        self.domain_skip = get(
            Domain,
            project=self.another_project,
            ssl_status=SSL_STATUS_INVALID,
            skip_validation=True,
            domain="docs.domain4.com",
        )

        self.domain_recently_expired = get(
            Domain,
            project=self.another_project,
            ssl_status=SSL_STATUS_PENDING,
            domain="docs.domain5.com",
        )
        self.domain_recently_expired.validation_process_start -= timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
        )
        self.domain_recently_expired.save()

        self.domain_expired = get(
            Domain,
            project=self.another_project,
            ssl_status=SSL_STATUS_PENDING,
            domain="docs.domain6.com",
        )
        self.domain_expired.validation_process_start -= timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD + 10
        )
        self.domain_expired.save()

    @mock.patch("readthedocs.notifications.email.send_email")
    def test_email_pending_emails(self, send_email):
        subject = "Pending configuration of custom domain"
        email_pending_custom_domains.delay(number_of_emails=3)
        self.assertEqual(send_email.call_count, 2)

        kwargs = send_email.call_args_list[0][1]
        self.assertEqual(kwargs["recipient"], self.user.email)
        self.assertTrue(kwargs["subject"].startswith(subject))
        self.assertIn(self.domain_recently_expired.domain, kwargs["subject"])

        kwargs = send_email.call_args_list[1][1]
        self.assertEqual(kwargs["recipient"], self.another_user.email)
        self.assertTrue(kwargs["subject"].startswith(subject))
        self.assertIn(self.domain_recently_expired.domain, kwargs["subject"])

    @mock.patch("readthedocs.notifications.email.send_email")
    def test_dont_send_email_on_given_days(self, send_email):
        now = timezone.now()
        days = [5, 8, 14, 16, 29, 31]
        for day in days:
            with mock.patch("django.utils.timezone.now") as nowmock:
                nowmock.return_value = now + timezone.timedelta(days=day)
                email_pending_custom_domains.delay(number_of_emails=3)
                send_email.assert_not_called()

    @mock.patch("readthedocs.notifications.email.send_email")
    def test_send_email_on_given_days(self, send_email):
        now = timezone.now()
        days = [7, 15, 30]
        for day in days:
            send_email.reset_mock()
            with mock.patch("django.utils.timezone.now") as nowmock:
                nowmock.return_value = now + timezone.timedelta(days=day)
                email_pending_custom_domains.delay(number_of_emails=3)
                self.assertEqual(send_email.call_count, 3)

                kwargs = send_email.call_args_list[0][1]
                self.assertEqual(kwargs["recipient"], self.user.email)
                self.assertIn(self.domain_pending.domain, kwargs["subject"])

                kwargs = send_email.call_args_list[1][1]
                self.assertEqual(kwargs["recipient"], self.user.email)
                self.assertIn(self.domain_invalid.domain, kwargs["subject"])

                kwargs = send_email.call_args_list[2][1]
                self.assertEqual(kwargs["recipient"], self.another_user.email)
                self.assertIn(self.domain_invalid.domain, kwargs["subject"])


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestTasksWithOrganizations(TestTasks):
    def setUp(self):
        super().setUp()
        self.organization = get(
            Organization,
            owners=[self.user],
            projects=[self.project, self.another_project],
        )
        self.team_a = get(
            Team,
            organization=self.organization,
            members=[self.user],
            projects=[self.project, self.another_project],
            access="admin",
        )
        self.team_b = get(
            Team,
            organization=self.organization,
            members=[self.user, self.another_user],
            projects=[self.another_project],
            access="admin",
        )
