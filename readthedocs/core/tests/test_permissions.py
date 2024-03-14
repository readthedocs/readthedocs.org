from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.core.permissions import AdminPermission
from readthedocs.organizations.constants import ADMIN_ACCESS, READ_ONLY_ACCESS
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestPermissionsWithOrganizations(TestCase):
    def setUp(self):
        self.owner = get(User)
        self.project = get(Project)
        self.organization = get(
            Organization, owners=[self.owner], projects=[self.project]
        )
        self.team = get(Team, organization=self.organization, access=ADMIN_ACCESS)
        self.team_read_only = get(
            Team, organization=self.organization, access=READ_ONLY_ACCESS
        )

        self.user_admin = get(User)
        self.user_on_same_team = get(User)
        self.user_read_only = get(User)

        self.organization.add_member(self.user_admin, self.team)
        self.organization.add_member(self.user_on_same_team, self.team)
        self.organization.add_member(self.user_read_only, self.team_read_only)

        self.another_owner = get(User)
        self.another_organization = get(Organization, owners=[self.another_owner])
        self.another_team = get(
            Team, organization=self.another_organization, access=ADMIN_ACCESS
        )
        self.another_team_read_only = get(
            Team, organization=self.another_organization, access=READ_ONLY_ACCESS
        )
        self.another_user_admin = get(User)
        self.another_user_read_only = get(User)

        self.another_organization.add_member(self.another_user_admin, self.another_team)
        self.another_organization.add_member(
            self.another_user_read_only, self.another_team_read_only
        )

    def test_members(self):
        users = AdminPermission.members(self.organization)
        self.assertQuerySetEqual(
            users,
            [self.owner, self.user_admin, self.user_read_only, self.user_on_same_team],
            ordered=False,
            transform=lambda x: x,
        )

        users = AdminPermission.members(self.another_organization)
        self.assertQuerySetEqual(
            users,
            [self.another_owner, self.another_user_admin, self.another_user_read_only],
            ordered=False,
            transform=lambda x: x,
        )

    def test_members_for_user(self):
        # Owner should be able to see all members.
        users = AdminPermission.members(self.organization, user=self.owner)
        self.assertQuerySetEqual(
            users,
            [self.owner, self.user_admin, self.user_read_only, self.user_on_same_team],
            ordered=False,
            transform=lambda x: x,
        )

        # User is able to see users that are on the same team, and owners.
        users = AdminPermission.members(self.organization, user=self.user_admin)
        self.assertQuerySetEqual(
            users,
            [self.owner, self.user_admin, self.user_on_same_team],
            ordered=False,
            transform=lambda x: x,
        )

        users = AdminPermission.members(self.organization, user=self.user_on_same_team)
        self.assertQuerySetEqual(
            users,
            [self.owner, self.user_admin, self.user_on_same_team],
            ordered=False,
            transform=lambda x: x,
        )

        users = AdminPermission.members(self.organization, user=self.user_read_only)
        self.assertQuerySetEqual(
            users,
            [self.owner, self.user_read_only],
            ordered=False,
            transform=lambda x: x,
        )
