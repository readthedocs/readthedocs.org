from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.models import Build, Version
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import (
    Organization,
    OrganizationOwner,
    Team,
    TeamMember,
)
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationTestCase(RequestFactoryTestMixin, TestCase):
    def setUp(self):
        self.owner = fixture.get(User)
        self.tester = fixture.get(User, username="tester")
        self.project = fixture.get(Project, slug="pip")

        self.organization = fixture.get(
            Organization,
            name="Mozilla",
            slug="mozilla",
            projects=[self.project],
            owners=[self.owner],
            stripe_id="1234",
        )
        self.client.force_login(user=self.owner)

    def add_owner(self, username="tester", test=True):
        data = {"username_or_email": username}
        resp = self.client.post(
            ("/organizations/mozilla/owners/add/".format(org=self.organization.slug)),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["location"],
                "/organizations/mozilla/owners/",
            )
        return resp

    def add_member(self, username="tester"):
        """
        Regression tests for removed functionality.

        Members are now a team only concept, where organization.members is now
        an aggregate function of all team members. Expect failures from form
        """

    def add_team(self, team="foobar", access="readonly", test=True):
        data = {
            "name": team,
            "slug": team,
            "access": access,
        }
        resp = self.client.post(
            ("/organizations/{org}/teams/add/".format(org=self.organization.slug)),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["location"],
                "/organizations/mozilla/teams/{}/".format(team),
            )
        return resp

    def add_project_to_team(self, team="foobar", projects=None, test=True):
        if projects is None:
            projects = [self.project.pk]
        elif isinstance(projects, list):
            projects = [project.pk for project in projects]

        data = {
            "projects": projects,
        }
        resp = self.client.post(
            (
                "/organizations/{org}/teams/{team}/projects/".format(
                    org=self.organization.slug, team=team
                )
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["location"],
                "/organizations/mozilla/teams/{}/".format(team),
            )
        return resp

    def add_team_member(self, username="tester", team="foobar", test=True):
        """Add organization team member."""
        data = {"member": username}
        resp = self.client.post(
            (
                "/organizations/{org}/teams/{team}/members/invite/".format(
                    org=self.organization.slug, team=team
                )
            ),
            data=data,
        )

        if test:
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["location"],
                "/organizations/mozilla/teams/{}/".format(team),
            )
        return resp


class OrganizationOwnerTests(OrganizationTestCase):
    def test_owner_add(self):
        """Test owner add form."""
        self.assertEqual(self.organization.owners.count(), 1)
        self.add_owner(username="tester")
        self.assertEqual(self.organization.owners.count(), 1)
        invitation = Invitation.objects.for_object(self.organization).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, User.objects.get(username="tester"))

    def test_owner_delete(self):
        """Test owner delete form."""
        user = get(User)
        self.organization.owners.add(user)
        owner = OrganizationOwner.objects.get(
            organization=self.organization,
            owner=user,
        )
        resp = self.client.post(
            "/organizations/mozilla/owners/{}/delete/".format(owner.pk),
            data={"username_or_email": user.username},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/owners/",
        )
        self.assertEqual(self.organization.owners.count(), 1)

    def test_organization_delete(self):
        """Removing an organization deletes all artifacts and leaf overs."""

        user_member = get(User)

        version = fixture.get(
            Version,
            project=self.project,
        )
        latest = self.project.versions.get(slug="latest")
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
        )
        team = fixture.get(
            Team,
            organization=self.organization,
        )
        member = fixture.get(
            TeamMember,
            team=team,
            member=user_member,
        )

        self.assertIn(self.organization, Organization.objects.all())
        self.assertIn(team, Team.objects.all())
        self.assertIn(member, TeamMember.objects.all())
        self.assertIn(self.project, Project.objects.all())
        self.assertIn(version, Version.objects.all())
        self.assertIn(build, Build.objects.all())

        with mock.patch(
            "readthedocs.projects.tasks.utils.clean_project_resources"
        ) as clean_project_resources:
            # Triggers a pre_delete signal that removes all leaf overs
            self.organization.delete()
            clean_project_resources.assert_called_once()

        self.assertNotIn(self.organization, Organization.objects.all())
        self.assertNotIn(team, Team.objects.all())
        self.assertNotIn(member, TeamMember.objects.all())
        self.assertNotIn(self.project, Project.objects.all())
        self.assertNotIn(version, Version.objects.all())
        self.assertNotIn(build, Build.objects.all())


class OrganizationMemberTests(OrganizationTestCase):
    def test_member_add_regression(self):
        """Test owner add from regression from previous functionality."""
        self.assertEqual(self.organization.members.count(), 1)
        self.add_member(username="tester")
        self.assertEqual(self.organization.members.count(), 1)
        self.assertEqual(self.organization.owners.count(), 1)

    def test_member_delete_regression(self):
        """Test member delete from regression from previous functionality."""
        self.test_member_add_regression()
        data = {"user": "tester"}
        resp = self.client.post(
            "/organizations/mozilla/members/delete/",
            data=data,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.organization.members.count(), 1)


class OrganizationTeamTests(OrganizationTestCase):
    def test_team_add(self):
        """Test member team add form."""
        self.add_team(team="foobar")
        self.assertEqual(self.organization.teams.count(), 1)

    def test_team_add_slug_conflict(self):
        """Add multiple teams with the same slug."""
        self.add_team(team="foobar")
        self.assertEqual(self.organization.teams.count(), 1)
        # Same name, same slug
        resp = self.add_team(team="foobar", test=False)
        self.assertEqual(self.organization.teams.count(), 1)
        self.assertEqual(resp.status_code, 200)
        # Different name, same slug
        resp = self.add_team(team="FOOBAR", test=False)
        self.assertEqual(self.organization.teams.count(), 2)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar-2/",
        )
        self.assertTrue(self.organization.teams.filter(slug="foobar").exists())
        self.assertTrue(
            self.organization.teams.filter(slug="foobar-2").exists(),
        )

    def test_team_delete(self):
        """Test team delete form."""
        self.test_team_add()
        resp = self.client.post("/organizations/mozilla/teams/foobar/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.organization.teams.count(), 0)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/",
        )

    def test_team_delete_regression(self):
        """Regression test old team delete form."""
        self.test_team_add()
        data = {"team": "foobar"}
        resp = self.client.post(
            "/organizations/mozilla/teams/delete/",
            data=data,
        )
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(self.organization.teams.count(), 1)


class OrganizationTeamMemberTests(OrganizationTestCase):
    def setUp(self):
        super().setUp()
        self.add_team(team="foobar")
        self.team = self.organization.teams.get(slug="foobar")
        self.assertEqual(self.organization.teams.count(), 1)

    def test_add_member_by_email(self):
        """Add member by email."""
        email = "foobar@example.com"
        data = {"username_or_email": email}
        self.client.force_login(self.owner)
        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar/",
        )
        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, email)

    def test_add_member_by_email_on_org_with_members(self):
        """Add member by email in organization with members already."""
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 0)

        user = fixture.get(User)

        # Create a team member that has no invite.
        fixture.get(
            TeamMember,
            team=self.team,
            member=user,
        )

        email = "foobar@example.com"
        self.client.force_login(self.owner)

        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data={"username_or_email": email},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar/",
        )
        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, email)

    def test_add_duplicate_member_by_email(self):
        """Add duplicate member by email."""
        email = "foobar@example.com"
        data = {"username_or_email": email}
        self.client.force_login(self.owner)
        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar/",
        )
        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, None)
        self.assertEqual(invitation.to_email, email)

        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_add_existing_user_by_username(self):
        data = {"username_or_email": "tester"}
        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar/",
        )
        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_email, None)
        self.assertEqual(invitation.to_user, User.objects.get(username="tester"))

    def test_invite_already_invited_member_by_username(self):
        data = {"username_or_email": "tester"}
        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "/organizations/mozilla/teams/foobar/",
        )
        self.assertEqual(self.team.members.count(), 0)

        invitation = Invitation.objects.for_object(self.team).get()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_email, None)
        self.assertEqual(invitation.to_user, User.objects.get(username="tester"))

        resp = self.client.post(
            "/organizations/mozilla/teams/foobar/members/invite/",
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 0)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 1)

    def test_invite_already_existing_member_by_username(self):
        user = get(User)
        self.team.members.add(user)
        self.assertEqual(self.team.members.count(), 1)

        resp = self.client.post(
            reverse(
                "organization_team_member_add",
                args=[self.organization.slug, self.team.slug],
            ),
            data={"username_or_email": user.username},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.team.members.count(), 1)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 0)

    @mock.patch("readthedocs.organizations.utils.send_email")
    def test_invite_user_from_the_same_org(self, send_email):
        owner = get(User)
        self.organization.owners.add(owner)

        member = get(User)
        self.add_team(team="another")
        team = Team.objects.get(slug="another")
        team.members.add(member)

        self.assertEqual(self.team.members.count(), 0)

        resp = self.client.post(
            reverse(
                "organization_team_member_add",
                args=[self.organization.slug, self.team.slug],
            ),
            data={"username_or_email": owner.username},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 1)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 0)
        send_email.assert_called_once()
        send_email.reset_mock()

        resp = self.client.post(
            reverse(
                "organization_team_member_add",
                args=[self.organization.slug, self.team.slug],
            ),
            data={"username_or_email": member.username},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 2)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 0)
        send_email.assert_called_once()

    @mock.patch("readthedocs.organizations.utils.send_email")
    def test_invite_myuself_to_team(self, send_email):
        self.assertEqual(self.team.members.count(), 0)
        resp = self.client.post(
            reverse(
                "organization_team_member_add",
                args=[self.organization.slug, self.team.slug],
            ),
            data={"username_or_email": self.owner.username},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.team.members.count(), 1)
        self.assertEqual(Invitation.objects.for_object(self.team).count(), 0)
        send_email.assert_not_called()
