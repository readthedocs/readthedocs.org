from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


class TestSignals(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.organization = get(
            Organization, owners=[self.user], projects=[self.project]
        )
        self.team = get(Team, organization=self.organization)
        self.another_user = get(User)

        for obj in [self.project, self.organization, self.team]:
            Invitation.objects.invite(
                from_user=self.user,
                obj=obj,
                to_user=self.another_user,
            )

    def test_delete_related_object(self):
        self.assertEqual(Invitation.objects.all().count(), 3)

        self.project.delete()
        self.assertEqual(Invitation.objects.all().count(), 2)

        self.team.delete()
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.organization.delete()
        self.assertEqual(Invitation.objects.all().count(), 0)
