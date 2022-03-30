from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog
from readthedocs.audit.tasks import delete_old_personal_audit_logs
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project


class AuditTasksTest(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(
            Project,
            slug="project",
        )
        self.organization = get(
            Organization,
            owners=[self.user],
            name="testorg",
        )
        self.organization.projects.add(self.project)

        self.another_user = get(User)
        self.another_project = get(
            Project,
            slug="another-project",
            users=[self.user],
        )

    @mock.patch("django.utils.timezone.now")
    def test_delete_old_personal_audit_logs(self, now_mock):
        now_mock.return_value = timezone.datetime(
            year=2021,
            month=5,
            day=5,
        )
        newer_date = timezone.datetime(
            year=2021,
            month=4,
            day=30,
        )
        middle_date = timezone.datetime(
            year=2021,
            month=4,
            day=5,
        )
        old_date = timezone.datetime(
            year=2021,
            month=3,
            day=20,
        )
        for date in [newer_date, middle_date, old_date]:
            for user in [self.user, self.another_user]:
                # Log attached to a project and organization.
                get(
                    AuditLog,
                    user=user,
                    project=self.project,
                    created=date,
                    action=AuditLog.PAGEVIEW,
                )
                # Log attached to a project only.
                get(
                    AuditLog,
                    user=user,
                    project=self.another_project,
                    created=date,
                    action=AuditLog.PAGEVIEW,
                )

                # Log attached to the user only.
                get(
                    AuditLog,
                    user=user,
                    created=date,
                    action=AuditLog.AUTHN,
                )

            # Log without a user.
            get(
                AuditLog,
                created=date,
                action=AuditLog.AUTHN_FAILURE,
            )

            # Log with a organization, and without a user.
            get(
                AuditLog,
                project=self.project,
                created=date,
                action=AuditLog.AUTHN_FAILURE,
            )

        self.assertEqual(AuditLog.objects.all().count(), 24)

        # We don't have logs older than 90 days.
        delete_old_personal_audit_logs(days=90)
        self.assertEqual(AuditLog.objects.all().count(), 24)

        # Only 5 logs can be deteled.
        delete_old_personal_audit_logs(days=30)
        self.assertEqual(AuditLog.objects.all().count(), 19)

        # Only 5 logs can be deteled.
        delete_old_personal_audit_logs(days=10)
        self.assertEqual(AuditLog.objects.all().count(), 14)

        # Only 5 logs can be deteled.
        delete_old_personal_audit_logs(days=1)
        self.assertEqual(AuditLog.objects.all().count(), 9)
