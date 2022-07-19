from unittest import mock

import django_dynamic_fixture as fixture
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.invitations.models import Invitation
from readthedocs.organizations import forms
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


class OrganizationTestCase(TestCase):

    def setUp(self):
        self.owner = fixture.get(User)
        self.user = fixture.get(User)
        self.project = fixture.get(Project)

        self.organization = fixture.get(
            Organization,
            name='Mozilla',
            slug='mozilla',
            owners=[self.owner],
            projects=[self.project],
            stripe_id='1234',
        )
        self.team = fixture.get(
            Team,
            name='foobar',
            slug='foobar',
            access='admin',
            organization=self.organization,
        )


class OrganizationTeamMemberFormTests(OrganizationTestCase):

    def test_add_team_member_by_name(self):
        request = mock.MagicMock(user=self.owner)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": self.user.username},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_add_duplicate_member_by_username(self):
        request = mock.MagicMock(user=self.owner)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": self.user.username},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        member_form = forms.OrganizationTeamMemberForm(
            {"user": self.user.username},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_add_team_member_by_email(self):
        """User with verified email is just added to team."""
        user = fixture.get(User)
        request = mock.MagicMock(user=self.owner)
        emailaddress = fixture.get(EmailAddress, user=user, verified=True)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": emailaddress.email},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        invitation = member_form.save()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, user)
        self.assertEqual(invitation.to_email, None)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_team_invite_unverified_email(self):
        """Team member with unverified email is invited by email."""
        user = fixture.get(User)
        fixture.get(EmailAddress, user=user, verified=False)

        request = mock.MagicMock(user=self.owner)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": user.email},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        invitation = member_form.save()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, user.email)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_fresh_member_by_email(self):
        """Add team member with email that is not associated with a user."""
        self.assertEqual(self.organization.teams.count(), 1)
        email = "testalsdkgh@example.com"
        request = mock.MagicMock(user=self.owner)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": email},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        invitation = member_form.save()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, email)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_duplicate_invite_by_email(self):
        """Add duplicate invite by email."""
        self.assertEqual(self.organization.teams.count(), 1)
        email = "non-existant@example.com"
        request = mock.MagicMock(user=self.owner)
        member_form = forms.OrganizationTeamMemberForm(
            {"user": email},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        first_invitation = member_form.save()

        member_form = forms.OrganizationTeamMemberForm(
            {"user": email},
            team=self.team,
            request=request,
        )
        self.assertTrue(member_form.is_valid())
        second_invitation = member_form.save()

        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(first_invitation, second_invitation)


class OrganizationSignupTest(OrganizationTestCase):

    def test_create_organization_with_empy_slug(self):
        data = {
            'name': '往事',
            'email': 'test@example.org',
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual('Invalid organization name: no slug generated', form.errors['name'][0])

    def test_create_organization_with_big_name(self):
        data = {
            'name': 'a' * 33,
            'email': 'test@example.org',
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('at most 32 characters', form.errors['name'][0])

    def test_create_organization_with_existent_slug(self):
        data = {
            'name': 'mozilla',
            'email': 'test@example.org',
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        # there is already an organization with the slug ``mozilla`` (lowercase)
        self.assertFalse(form.is_valid())

    def test_create_organization_with_nonexistent_slug(self):
        data = {
            'name': 'My New Organization',
            'email': 'test@example.org',
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertTrue(form.is_valid())
