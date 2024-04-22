import django_dynamic_fixture as fixture
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from readthedocs.core.notifications import MESSAGE_EMAIL_VALIDATION_PENDING
from readthedocs.notifications.constants import CANCELLED, UNREAD
from readthedocs.notifications.models import Notification
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import MESSAGE_PROJECT_SKIP_BUILDS
from readthedocs.subscriptions.notifications import MESSAGE_ORGANIZATION_DISABLED


class TestSignals(TestCase):
    def test_project_skip_builds(self):
        project = fixture.get(Project)

        self.assertEqual(project.notifications.count(), 0)
        project.skip = True
        project.save()

        self.assertEqual(project.notifications.count(), 1)

        notification = project.notifications.first()
        self.assertEqual(notification.message_id, MESSAGE_PROJECT_SKIP_BUILDS)
        self.assertEqual(notification.state, UNREAD)

        project.skip = False
        project.save()

        notification.refresh_from_db()
        self.assertEqual(project.notifications.count(), 1)
        self.assertEqual(notification.message_id, MESSAGE_PROJECT_SKIP_BUILDS)
        self.assertEqual(notification.state, CANCELLED)

    def test_organization_disabled(self):
        organization = fixture.get(Organization)

        self.assertEqual(organization.notifications.count(), 0)
        organization.disabled = True
        organization.save()

        self.assertEqual(organization.notifications.count(), 1)

        notification = organization.notifications.first()
        self.assertEqual(notification.message_id, MESSAGE_ORGANIZATION_DISABLED)
        self.assertEqual(notification.state, UNREAD)

        organization.disabled = False
        organization.save()

        notification.refresh_from_db()
        self.assertEqual(organization.notifications.count(), 1)
        self.assertEqual(notification.message_id, MESSAGE_ORGANIZATION_DISABLED)
        self.assertEqual(notification.state, CANCELLED)

    def test_user_email_verified(self):
        user = fixture.get(User)
        emailaddress = fixture.get(
            EmailAddress,
            user=user,
            primary=True,
            verified=False,
        )

        self.assertEqual(Notification.objects.for_user(user, resource="all").count(), 1)

        notification = Notification.objects.for_user(user, resource="all").first()
        self.assertEqual(notification.message_id, MESSAGE_EMAIL_VALIDATION_PENDING)
        self.assertEqual(notification.state, UNREAD)

        emailaddress.verified = True
        emailaddress.save()

        notification.refresh_from_db()

        # 0 notifications to show to the user (none UNREAD)
        self.assertEqual(Notification.objects.for_user(user, resource="all").count(), 0)

        # 1 notification exists attached to this user, tho
        self.assertEqual(
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(user),
                attached_to_id=user.id,
            ).count(),
            1,
        )
        self.assertEqual(notification.message_id, MESSAGE_EMAIL_VALIDATION_PENDING)
        self.assertEqual(notification.state, CANCELLED)
