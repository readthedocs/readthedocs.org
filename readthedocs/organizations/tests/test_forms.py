import django_dynamic_fixture as fixture
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase

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
        member_form = forms.OrganizationTeamMemberForm(
            {'member': self.user.username},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        self.assertEqual(self.team.members.count(), 1)

    def test_add_duplicate_member_by_username(self):
        member_form = forms.OrganizationTeamMemberForm(
            {'member': self.user.username},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        member_form = forms.OrganizationTeamMemberForm(
            {'member': self.user.username},
            team=self.team,
        )
        self.assertFalse(member_form.is_valid())
        self.assertEqual(self.team.members.count(), 1)

    def test_add_team_member_by_email(self):
        """User with verified email is just added to team."""
        user = fixture.get(User)
        emailaddress = fixture.get(EmailAddress, user=user, verified=True)
        member_form = forms.OrganizationTeamMemberForm(
            {'member': emailaddress.email},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        teammember = member_form.save()
        self.assertIsNone(teammember.invite)
        self.assertEqual(teammember.member, user)
        self.assertEqual(self.team.members.count(), 1)
        self.assertEqual(self.team.invites.count(), 0)

    def test_add_team_invite_unverified_email(self):
        """Team member with unverified email is invited by email."""
        user = fixture.get(User)
        __ = fixture.get(EmailAddress, user=user, verified=False)

        member_form = forms.OrganizationTeamMemberForm(
            {'member': user.email},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        teammember = member_form.save()
        self.assertIsNone(teammember.member)
        self.assertEqual(teammember.invite.email, user.email)
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(self.team.invites.count(), 1)

    def test_add_fresh_member_by_email(self):
        """Add team member with email that is not associated with a user."""
        self.assertEqual(self.organization.teams.count(), 1)
        member_form = forms.OrganizationTeamMemberForm(
            {'member': 'testalsdkgh@example.com'},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(self.team.invites.count(), 1)

    def test_add_duplicate_invite_by_email(self):
        """Add duplicate invite by email."""
        self.assertEqual(self.organization.teams.count(), 1)
        member_form = forms.OrganizationTeamMemberForm(
            {'member': 'non-existant@example.com'},
            team=self.team,
        )
        self.assertTrue(member_form.is_valid())
        member_form.save()
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(self.team.invites.count(), 1)
        member_form = forms.OrganizationTeamMemberForm(
            {'member': 'non-existant@example.com'},
            team=self.team,
        )
        self.assertFalse(member_form.is_valid())


class OrganizationSignupTest(OrganizationTestCase):

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
