from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from readthedocs.builds.models import Build, Version
from readthedocs.organizations import views
from readthedocs.organizations.models import (
    Organization,
    OrganizationOwner,
    Team,
    TeamInvite,
    TeamMember,
)
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationTestCase(RequestFactoryTestMixin, TestCase):

    def setUp(self):
        self.owner = fixture.get(User)
        self.tester = fixture.get(User, username='tester')
        self.project = fixture.get(Project, slug='pip')

        self.organization = fixture.get(
            Organization,
            name='Mozilla',
            slug='mozilla',
            projects=[self.project],
            owners=[self.owner],
            stripe_id='1234',
        )
        self.client.force_login(user=self.owner)

    def add_owner(self, username='tester', test=True):
        data = {'owner': username}
        resp = self.client.post(
            (
                '/organizations/mozilla/owners/add/'
                .format(org=self.organization.slug)
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp['location'],
                '/organizations/mozilla/owners/',
            )
        return resp

    def add_member(self, username='tester'):
        """
        Regression tests for removed functionality.

        Members are now a team only concept, where organization.members is now
        an aggregate function of all team members. Expect failures from form
        """

    def add_team(self, team='foobar', access='readonly', test=True):
        data = {
            'name': team,
            'slug': team,
            'access': access,
        }
        resp = self.client.post(
            (
                '/organizations/{org}/teams/add/'
                .format(org=self.organization.slug)
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp['location'],
                '/organizations/mozilla/teams/{}/'.format(team),
            )
        return resp

    def add_project_to_team(self, team='foobar', projects=None, test=True):
        if projects is None:
            projects = [self.project.pk]
        elif isinstance(projects, list):
            projects = [project.pk for project in projects]

        data = {
            'projects': projects,
        }
        resp = self.client.post(
            (
                '/organizations/{org}/teams/{team}/projects/'
                .format(org=self.organization.slug, team=team)
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp['location'],
                '/organizations/mozilla/teams/{}/'.format(team),
            )
        return resp

    def add_team_member(self, username='tester', team='foobar', test=True):
        """Add organization team member."""
        data = {'member': username}
        resp = self.client.post(
            (
                '/organizations/{org}/teams/{team}/members/invite/'
                .format(org=self.organization.slug, team=team)
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp['location'],
                '/organizations/mozilla/teams/{}/'.format(team),
            )
        return resp


class OrganizationOwnerTests(OrganizationTestCase):

    def test_owner_add(self):
        """Test owner add form."""
        self.assertEqual(self.organization.owners.count(), 1)
        self.add_owner(username='tester')
        self.assertEqual(self.organization.owners.count(), 2)

    def test_owner_delete(self):
        """Test owner delete form."""
        self.test_owner_add()
        data = {'user': 'tester'}
        user = self.organization.owners.get(username='tester')
        owner = OrganizationOwner.objects.get(
            organization=self.organization,
            owner=user,
        )
        resp = self.client.post(
            '/organizations/mozilla/owners/{}/delete/'.format(owner.pk),
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/owners/',
        )
        self.assertEqual(self.organization.owners.count(), 1)

    def test_organization_delete(self):
        """Removing an organization deletes all artifacts and leaf overs."""

        version = fixture.get(
            Version,
            project=self.project,
        )
        latest = self.project.versions.get(slug='latest')
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
        )
        team = fixture.get(
            Team,
            organization=self.organization,
        )
        invite = fixture.get(
            TeamInvite,
            team=team,
            organization=self.organization,
        )
        member = fixture.get(
            TeamMember,
            team=team,
            invite=invite,
        )

        self.assertIn(self.organization, Organization.objects.all())
        self.assertIn(team, Team.objects.all())
        self.assertIn(invite, TeamInvite.objects.all())
        self.assertIn(member, TeamMember.objects.all())
        self.assertIn(self.project, Project.objects.all())
        self.assertIn(version, Version.objects.all())
        self.assertIn(build, Build.objects.all())

        with mock.patch('readthedocs.projects.tasks.utils.clean_project_resources') as clean_project_resources:
            # Triggers a pre_delete signal that removes all leaf overs
            self.organization.delete()
            clean_project_resources.assert_called_once()

        self.assertNotIn(self.organization, Organization.objects.all())
        self.assertNotIn(team, Team.objects.all())
        self.assertNotIn(invite, TeamInvite.objects.all())
        self.assertNotIn(member, TeamMember.objects.all())
        self.assertNotIn(self.project, Project.objects.all())
        self.assertNotIn(version, Version.objects.all())
        self.assertNotIn(build, Build.objects.all())


class OrganizationMemberTests(OrganizationTestCase):

    def test_member_add_regression(self):
        """Test owner add from regression from previous functionality."""
        self.assertEqual(self.organization.members.count(), 1)
        self.add_member(username='tester')
        self.assertEqual(self.organization.members.count(), 1)
        self.assertEqual(self.organization.owners.count(), 1)

    def test_member_delete_regression(self):
        """Test member delete from regression from previous functionality."""
        self.test_member_add_regression()
        data = {'user': 'tester'}
        resp = self.client.post(
            '/organizations/mozilla/members/delete/',
            data=data,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.organization.members.count(), 1)


class OrganizationTeamTests(OrganizationTestCase):

    def test_team_add(self):
        """Test member team add form."""
        self.add_team(team='foobar')
        self.assertEqual(self.organization.teams.count(), 1)

    def test_team_add_slug_conflict(self):
        """Add multiple teams with the same slug."""
        self.add_team(team='foobar')
        self.assertEqual(self.organization.teams.count(), 1)
        # Same name, same slug
        resp = self.add_team(team='foobar', test=False)
        self.assertEqual(self.organization.teams.count(), 1)
        self.assertEqual(resp.status_code, 200)
        # Different name, same slug
        resp = self.add_team(team='FOOBAR', test=False)
        self.assertEqual(self.organization.teams.count(), 2)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar-2/',
        )
        self.assertTrue(self.organization.teams.filter(slug='foobar').exists())
        self.assertTrue(
            self.organization.teams.filter(slug='foobar-2').exists(),
        )

    def test_team_delete(self):
        """Test team delete form."""
        self.test_team_add()
        resp = self.client.post('/organizations/mozilla/teams/foobar/delete/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.organization.teams.count(), 0)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/',
        )

    def test_team_delete_regression(self):
        """Regression test old team delete form."""
        self.test_team_add()
        data = {'team': 'foobar'}
        resp = self.client.post(
            '/organizations/mozilla/teams/delete/',
            data=data,
        )
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(self.organization.teams.count(), 1)


class OrganizationTeamMemberTests(OrganizationTestCase):

    def setUp(self):
        super().setUp()
        self.add_team(team='foobar')
        self.team = self.organization.teams.get(slug='foobar')
        self.assertEqual(self.organization.teams.count(), 1)

    def test_add_member_by_email(self):
        """Add member by email."""
        data = {'member': 'foobar@example.com'}
        req = self.request(
            'post',
            '/organizations/mozilla/teams/foobar/members/invite/',
            user=self.owner,
            data=data,
        )
        view = views.private.AddOrganizationTeamMember.as_view()
        resp = view(req, slug=self.organization.slug, team=self.team.slug)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar/',
        )
        self.assertEqual(self.team.invites.count(), 1)

    def test_add_member_by_email_on_org_with_members(self):
        """
        Add member by email in organization with members already

        If there is at least one ``TeamMember.invite=None`` the invitation
        should be sent anyways instead of failing with a form validation "An
        invitation was already sent".
        """
        self.assertEqual(self.team.invites.count(), 0)

        user = fixture.get(User)

        # Create a team member that has no invite
        fixture.get(
            TeamMember,
            team=self.team,
            member=user,
            invite=None,  # force
        )

        data = {'member': 'foobar@example.com'}
        req = self.request(
            'post',
            '/organizations/mozilla/teams/foobar/members/invite/',
            user=self.owner,
            data=data,
        )
        view = views.private.AddOrganizationTeamMember.as_view()
        resp = view(req, slug=self.organization.slug, team=self.team.slug)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar/',
        )
        self.assertEqual(self.team.invites.count(), 1)


    def test_add_duplicate_member_by_email(self):
        """Add duplicate member by email."""
        data = {'member': 'foobar@example.com'}
        req = self.request(
            'post',
            '/organizations/mozilla/teams/foobar/members/invite/',
            user=self.owner,
            data=data,
        )
        view = views.private.AddOrganizationTeamMember.as_view()
        resp = view(req, slug=self.organization.slug, team=self.team.slug)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar/',
        )
        self.assertEqual(self.team.invites.count(), 1)
        resp = self.client.post(
            '/organizations/mozilla/teams/foobar/members/invite/',
            data=data,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.team.invites.count(), 1)

    def test_add_existing_member_by_username(self):
        data = {'member': 'tester'}
        resp = self.client.post(
            '/organizations/mozilla/teams/foobar/members/invite/',
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar/',
        )
        self.assertEqual(self.team.members.count(), 1)

    def test_add_already_existing_member_by_username(self):
        data = {'member': 'tester'}
        resp = self.client.post(
            '/organizations/mozilla/teams/foobar/members/invite/',
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['location'],
            '/organizations/mozilla/teams/foobar/',
        )
        self.assertEqual(self.team.members.count(), 1)
        resp = self.client.post(
            '/organizations/mozilla/teams/foobar/members/invite/',
            data=data,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.team.members.count(), 1)
