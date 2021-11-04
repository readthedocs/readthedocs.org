from allauth.account.views import SignupView
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.organizations.models import (
    Organization,
    Team,
    TeamInvite,
    TeamMember,
)
from readthedocs.organizations.views import public as public_views
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationViewTests(RequestFactoryTestMixin, TestCase):

    """Organization views tests."""

    def setUp(self):
        self.owner = get(User, username='owner', email='owner@example.com')
        self.owner.emailaddress_set.create(email=self.owner.email, verified=True)
        self.project = get(Project)
        self.organization = get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.team = get(Team, organization=self.organization)
        self.client.force_login(self.owner)

    def test_delete(self):
        """Delete organization on post."""
        resp = self.client.post(
            reverse('organization_delete', args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 302)

        self.assertFalse(Organization.objects
                         .filter(pk=self.organization.pk)
                         .exists())
        self.assertFalse(Team.objects
                         .filter(pk=self.team.pk)
                         .exists())
        self.assertFalse(Project.objects
                        .filter(pk=self.project.pk)
                        .exists())

    def test_add_owner(self):
        url = reverse('organization_owner_add', args=[self.organization])
        user = get(User, username='test-user', email='test-user@example.com')
        user.emailaddress_set.create(email=user.email, verified=False)

        user_b = get(User, username='test-user-b', email='test-user-b@example.com')
        user_b.emailaddress_set.create(email=user_b.email, verified=True)

        # Adding an already owner.
        for username in [self.owner.username, self.owner.email]:
            resp = self.client.post(url, data={'owner': username})
            form = resp.context_data['form']
            self.assertFalse(form.is_valid())
            self.assertIn('is already an owner', form.errors['owner'][0])

        # Unknown user.
        resp = self.client.post(url, data={'owner': 'non-existent'})
        form = resp.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertIn('does not exist', form.errors['owner'][0])

        # From an unverified email.
        resp = self.client.post(url, data={'owner': user.email})
        form = resp.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertIn('does not exist', form.errors['owner'][0])

        # Using a username.
        self.assertFalse(user in self.organization.owners.all())
        resp = self.client.post(url, data={'owner': user.username})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(user in self.organization.owners.all())

        # Using an email.
        self.assertFalse(user_b in self.organization.owners.all())
        resp = self.client.post(url, data={'owner': user_b.email})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(user_b in self.organization.owners.all())


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationInviteViewTests(RequestFactoryTestMixin, TestCase):

    """Tests for invite handling in views."""

    def setUp(self):
        self.owner = get(User)
        self.organization = get(
            Organization,
            owners=[self.owner],
        )
        self.team = get(Team, organization=self.organization)

    def tearDown(self):
        cache.clear()

    def test_redemption_by_authed_user(self):
        user = get(User)
        invite = get(
            TeamInvite, email=user.email, team=self.team,
            organization=self.organization,
        )
        team_member = get(
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
        invite = get(
            TeamInvite, email=email, team=self.team,
            organization=self.organization,
        )
        team_member = get(
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
        user = get(User)
        invite = get(
            TeamInvite, email=user.email, team=self.team,
            organization=self.organization,
        )
        team_member_a = get(
            TeamMember,
            invite=None,
            member=user,
            team=self.team,
        )
        team_member_b = get(
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


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationSignupTestCase(TestCase):

    def tearDown(self):
        cache.clear()

    def test_organization_signup(self):
        self.assertEqual(Organization.objects.count(), 0)
        user = get(User)
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
