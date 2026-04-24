import django_dynamic_fixture as fixture
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from readthedocs.invitations.models import Invitation
from readthedocs.organizations import forms
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationTestCase(TestCase):
    def setUp(self):
        self.owner = fixture.get(User)
        self.user = fixture.get(User)
        self.project = fixture.get(Project)

        self.organization = fixture.get(
            Organization,
            name="Mozilla",
            slug="mozilla",
            owners=[self.owner],
            projects=[self.project],
            stripe_id="1234",
        )
        self.team = fixture.get(
            Team,
            name="foobar",
            slug="foobar",
            access="admin",
            organization=self.organization,
        )
        self.client.force_login(self.owner)


class OrganizationTeamMemberFormTests(OrganizationTestCase):
    def test_add_team_member_by_name(self):
        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": self.user.username})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_add_duplicate_member_by_username(self):
        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": self.user.username})
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(url, data={"username_or_email": self.user.username})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_add_team_member_by_email(self):
        """User with verified email is just added to team."""
        user = fixture.get(User)
        emailaddress = fixture.get(EmailAddress, user=user, verified=True)

        self.assertEqual(Invitation.objects.all().count(), 0)

        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": emailaddress.email})
        self.assertEqual(resp.status_code, 302)

        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, user)
        self.assertEqual(invitation.to_email, None)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_team_invite_unverified_email(self):
        """Team member with unverified email is invited by email."""
        user = fixture.get(User)
        fixture.get(EmailAddress, user=user, verified=False)

        self.assertEqual(Invitation.objects.all().count(), 0)

        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": user.email})
        self.assertEqual(resp.status_code, 302)

        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, user.email)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_fresh_member_by_email(self):
        """Add team member with email that is not associated with a user."""
        self.assertEqual(self.organization.teams.count(), 1)
        email = "testalsdkgh@example.com"

        self.assertEqual(Invitation.objects.all().count(), 0)

        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": email})
        self.assertEqual(resp.status_code, 302)

        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, email)
        self.assertEqual(self.team.members.count(), 0)

    def test_add_duplicate_invite_by_email(self):
        """Add duplicate invite by email."""
        self.assertEqual(self.organization.teams.count(), 1)
        email = "non-existant@example.com"

        self.assertEqual(Invitation.objects.all().count(), 0)

        url = reverse(
            "organization_team_member_add",
            args=[self.organization.slug, self.team.slug],
        )
        resp = self.client.post(url, data={"username_or_email": email})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(Invitation.objects.all().count(), 1)

        resp = self.client.post(url, data={"username_or_email": email})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(Invitation.objects.all().count(), 1)
        self.assertEqual(self.team.members.count(), 0)


class OrganizationSignupTest(OrganizationTestCase):
    def test_create_organization_with_empty_slug(self):
        data = {
            "name": "往事",
            "email": "test@example.org",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            "This field is required.", form.errors["slug"][0]
        )

    def test_create_organization_with_invalid_unicode_slug(self):
        data = {
            "name": "往事",
            "email": "test@example.org",
            "slug": "-",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            "Invalid slug, use more valid characters.", form.errors["slug"][0]
        )

    def test_create_organization_with_big_name(self):
        data = {
            "name": "a" * 33,
            "email": "test@example.org",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("at most 32 characters", form.errors["name"][0])

    def test_create_organization_with_existent_slug(self):
        data = {
            "name": "Fauxzilla",
            "email": "test@example.org",
            "slug": "mozilla",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        # there is already an organization with the slug ``mozilla`` (lowercase)
        self.assertFalse(form.is_valid())
        self.assertEqual("Slug is already used by another organization", form.errors["slug"][0])

    def test_create_organization_with_nonexistent_slug(self):
        data = {
            "name": "My New Organization",
            "email": "test@example.org",
            "slug": "my-new-organization",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertTrue(form.is_valid())
        organization = form.save()
        self.assertEqual(Organization.objects.filter(slug="my-new-organization").count(), 1)

    def test_create_organization_with_invalid_slug(self):
        data = {
            "name": "My Org",
            "email": "test@example.org",
            "slug": "invalid-<slug>",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("consisting of letters, numbers", form.errors["slug"][0])

    def test_create_organization_with_dns_invalid_slug(self):
        data = {
            "name": "My Org",
            "email": "test@example.org",
            "slug": "-invalid_slug-",
        }
        form = forms.OrganizationSignupForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid slug, use suggested slug 'invalid-slug' instead", form.errors["slug"][0])
