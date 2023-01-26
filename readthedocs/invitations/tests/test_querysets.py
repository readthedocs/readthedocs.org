from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


class TestQuerysets(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.organization = get(
            Organization, owners=[self.user], projects=[self.project]
        )
        self.team = get(Team, organization=self.organization)
        self.another_user = get(User)
        self.email = "test@example.com"

    @mock.patch("readthedocs.invitations.backends.send_email")
    def test_invite_twice_email(self, send_email):
        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_email=self.email,
            obj=self.project,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)
        send_email.assert_called_once()
        send_email.reset_mock()

        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_email=self.email,
            obj=self.project,
        )
        self.assertFalse(created)
        self.assertFalse(invitation.expired)
        send_email.assert_not_called()

        self.assertEqual(Invitation.objects.all().count(), 1)

    @mock.patch("readthedocs.invitations.backends.send_email")
    def test_invite_twice_user(self, send_email):
        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_user=self.another_user,
            obj=self.project,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)
        send_email.assert_called_once()
        send_email.reset_mock()

        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_user=self.another_user,
            obj=self.project,
        )
        self.assertFalse(created)
        self.assertFalse(invitation.expired)
        send_email.assert_not_called()

        self.assertEqual(Invitation.objects.all().count(), 1)

    def test_invite_to_organization(self):
        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_user=self.another_user,
            obj=self.organization,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)

        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_email=self.email,
            obj=self.organization,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)

        self.assertEqual(Invitation.objects.all().count(), 2)

    def test_invite_to_team(self):
        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_user=self.another_user,
            obj=self.team,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)

        invitation, created = Invitation.objects.invite(
            from_user=self.user,
            to_email=self.email,
            obj=self.team,
        )
        self.assertTrue(created)
        self.assertFalse(invitation.expired)
        self.assertIsNotNone(invitation.backend)

        self.assertEqual(Invitation.objects.all().count(), 2)

    def test_querysets(self):
        expired = timezone.now() - timezone.timedelta(
            days=settings.RTD_INVITATIONS_EXPIRATION_DAYS + 3
        )

        Invitation.objects.create(
            from_user=self.user,
            to_user=self.another_user,
            object=self.project,
        )

        Invitation.objects.create(
            from_user=self.user,
            to_user=self.another_user,
            object=self.organization,
            expiration_date=expired,
        )

        Invitation.objects.create(
            from_user=self.user,
            to_user=self.another_user,
            object=self.team,
        )

        Invitation.objects.create(
            from_user=self.user,
            to_email=self.email,
            object=self.project,
            expiration_date=expired,
        )

        Invitation.objects.create(
            from_user=self.user,
            to_email=self.email,
            object=self.organization,
        )

        Invitation.objects.create(
            from_user=self.user,
            to_email=self.email,
            object=self.team,
        )
        self.assertEqual(Invitation.objects.expired().count(), 2)

        self.assertEqual(Invitation.objects.all().count(), 6)
        self.assertEqual(Invitation.objects.expired().count(), 2)
        self.assertEqual(Invitation.objects.pending().count(), 4)

        self.assertEqual(Invitation.objects.pending(self.project).count(), 1)
        self.assertEqual(Invitation.objects.expired(self.project).count(), 1)

        self.assertEqual(Invitation.objects.pending(self.organization).count(), 1)
        self.assertEqual(Invitation.objects.expired(self.organization).count(), 1)

        self.assertEqual(Invitation.objects.pending(self.team).count(), 2)
        self.assertEqual(Invitation.objects.expired(self.team).count(), 0)

        self.assertEqual(Invitation.objects.for_object(self.project).count(), 2)
        self.assertEqual(Invitation.objects.for_object(self.organization).count(), 2)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 2)
