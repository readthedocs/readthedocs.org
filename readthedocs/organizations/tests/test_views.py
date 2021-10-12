import django_dynamic_fixture as fixture
from allauth.account.views import SignupView
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from readthedocs.organizations.models import (
    Organization,
    Team,
    TeamInvite,
    TeamMember,
)
from readthedocs.organizations.views import private as private_views
from readthedocs.organizations.views import public as public_views
from readthedocs.projects.models import Project
from readthedocs.sso.models import SSOIntegration
from readthedocsinc.core.tests.utils import RequestFactoryTestMixin


class OrganizationViewTests(RequestFactoryTestMixin, TestCase):

    """Organization views tests."""

    def setUp(self):
        self.owner = fixture.get(User)
        self.project = fixture.get(Project)
        self.organization = fixture.get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.team = fixture.get(Team, organization=self.organization)

    def test_delete(self):
        """Delete organization on post."""
        req = self.request(
            'post',
            '/organizations/{}/delete/'.format(self.organization.slug),
            user=self.owner,
        )
        view = private_views.DeleteOrganization.as_view()
        resp = view(req, slug=self.organization.slug)

        self.assertFalse(Organization.objects
                         .filter(pk=self.organization.pk)
                         .exists())
        self.assertFalse(Team.objects
                         .filter(pk=self.team.pk)
                         .exists())
        self.assertFalse(Project.objects
                        .filter(pk=self.project.pk)
                        .exists())


class OrganizationInviteViewTests(RequestFactoryTestMixin, TestCase):

    """Tests for invite handling in views."""

    def setUp(self):
        self.owner = fixture.get(User)
        self.organization = fixture.get(
            Organization,
            owners=[self.owner],
        )
        self.team = fixture.get(Team, organization=self.organization)

    def tearDown(self):
        cache.clear()

    def test_redemption_by_authed_user(self):
        user = fixture.get(User)
        invite = fixture.get(
            TeamInvite, email=user.email, team=self.team,
            organization=self.organization,
        )
        team_member = fixture.get(
            TeamMember,
            invite=invite,
            member=None,
            team=self.team,
        )

        req = self.request(
            'get',
            '/organizations/invite/{}/redeem'.format(invite.hash),
            user=user,
        )
        view = public_views.UpdateOrganizationTeamMember.as_view()
        view(req, hash=invite.hash)

        ret_teammember = TeamMember.objects.get(member=user)
        self.assertIsNone(ret_teammember.invite)
        self.assertEqual(ret_teammember, team_member)
        with self.assertRaises(TeamInvite.DoesNotExist):
            TeamInvite.objects.get(pk=invite.pk)

    def test_redemption_by_unauthed_user(self):
        """Redemption on triggers on user signup."""
        email = 'non-existant-9238723@example.com'
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=email)
        invite = fixture.get(
            TeamInvite, email=email, team=self.team,
            organization=self.organization,
        )
        team_member = fixture.get(
            TeamMember,
            invite=invite,
            member=None,
            team=self.team,
        )

        req = self.request(
            'get',
            '/organizations/invite/{}/redeem'.format(invite.hash),
        )
        view = public_views.UpdateOrganizationTeamMember.as_view()
        view(req, hash=invite.hash)

        self.assertEqual(team_member.invite, invite)
        self.assertIsNone(team_member.member)
        self.assertEqual(req.session['invite'], invite.pk)
        self.assertEqual(req.session['invite:allow_signup'], True)
        self.assertEqual(req.session['invite:email'], email)

        # This cookie makes the EmailAddress be verified after signing up with
        # the same email address the user was invited. This is done
        # automatically by django-allauth
        self.assertEqual(req.session['account_verified_email'], email)

        session = req.session

        # Test signup view
        req = self.request(
            'post',
            '/accounts/signup',
            data={
                'username': 'test-92867',
                'email': email,
                'password1': 'password',
                'password2': 'password',
                'confirmation_key': 'foo',
            },
            session=session,
        )
        resp = SignupView.as_view()(req)

        self.assertEqual(resp.status_code, 302)

        ret_teammember = TeamMember.objects.get(member__email=email)
        self.assertIsNone(ret_teammember.invite)
        self.assertEqual(ret_teammember, team_member)
        with self.assertRaises(TeamInvite.DoesNotExist):
            TeamInvite.objects.get(pk=invite.pk)

        self.assertTrue(
            User.objects.get(email=email)
            .emailaddress_set.filter(verified=True)
            .exists()
        )

    def test_redemption_by_dulpicate_user(self):
        user = fixture.get(User)
        invite = fixture.get(
            TeamInvite, email=user.email, team=self.team,
            organization=self.organization,
        )
        team_member_a = fixture.get(
            TeamMember,
            invite=None,
            member=user,
            team=self.team,
        )
        team_member_b = fixture.get(
            TeamMember,
            invite=invite,
            member=None,
            team=self.team,
        )
        self.assertEqual(TeamMember.objects.filter(member=user).count(), 1)

        req = self.request(
            'get',
            '/organizations/invite/{}/redeem'.format(invite.hash),
            user=user,
        )
        view = public_views.UpdateOrganizationTeamMember.as_view()
        view(req, hash=invite.hash)

        self.assertEqual(TeamMember.objects.filter(member=user).count(), 1)
        self.assertEqual(TeamMember.objects.filter(invite=invite).count(), 0)
        with self.assertRaises(TeamInvite.DoesNotExist):
            TeamInvite.objects.get(pk=invite.pk)

    def test_redemption_to_organization_with_vcs_sso(self):
        user = fixture.get(User)
        invite = fixture.get(
            TeamInvite,
            email=user.email,
            team=self.team,
            organization=self.organization,
        )
        member = fixture.get(
            TeamMember,
            invite=invite,
            member=None,
            team=self.team,
        )
        fixture.get(
            SSOIntegration,
            organization=self.organization,
            provider=SSOIntegration.PROVIDER_EMAIL,
        )
        response = self.client.get(
            reverse('organization_invite_redeem', args=[invite.hash]),
        )
        self.assertRedirects(
            response,
            '/accounts/signup/'
            f'?organization={self.organization.slug}'
        )

    def test_redemption_to_organization_with_google_sso(self):
        user = fixture.get(User)
        invite = fixture.get(
            TeamInvite,
            email=user.email,
            team=self.team,
            organization=self.organization,
        )
        member = fixture.get(
            TeamMember,
            invite=invite,
            member=None,
            team=self.team,
        )
        fixture.get(
            SSOIntegration,
            organization=self.organization,
            provider=SSOIntegration.PROVIDER_ALLAUTH,
        )
        response = self.client.get(
            reverse('organization_invite_redeem', args=[invite.hash]),
        )
        self.assertRedirects(
            response,
            '/accounts/signup/'
            f'?organization={self.organization.slug}'
        )


class OrganizationSignupTestCase(TestCase):

    def tearDown(self):
        cache.clear()

    def test_organization_signup(self):
        self.assertEqual(Organization.objects.count(), 0)
        user = fixture.get(User)
        self.client.force_login(user)
        data = {
            'name': 'Testing Organization',
            'email': 'billing@email.com',
        }
        resp = self.client.post(reverse('organization_create'), data=data)
        self.assertEqual(Organization.objects.count(), 1)

        org = Organization.objects.first()
        self.assertEqual(org.name, 'Testing Organization')
        self.assertEqual(org.email, 'billing@email.com')
        self.assertRedirects(
            resp,
            reverse('organization_detail', kwargs={'slug': org.slug}),
        )
