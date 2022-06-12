from unittest.mock import call, patch

from django import urls
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization, Team, TeamMember


class OrganizationAdminActionsTest(TestCase):
    """Organization admin action tests."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = get(User, is_staff=True, is_superuser=True)
        cls.user = get(User)
        cls.owner = get(User)
        cls.organization = get(
            Organization,
            owners=[cls.owner],
        )
        get(
            TeamMember,
            member=cls.user,
            team=get(Team, organization=cls.organization),
        )

    def setUp(self):
        self.client.force_login(self.admin)

    @patch("readthedocs.organizations.admin.sync_remote_repositories")
    def test_sync_remote_repositories_action(self, mock_sync_remote_repositories):
        action_data = {
            ACTION_CHECKBOX_NAME: [self.organization.pk],
            "action": "sync_remote_repositories_action",
            "index": 0,
        }
        self.client.post(
            urls.reverse("admin:organizations_organization_changelist"),
            action_data,
        )
        mock_sync_remote_repositories.delay.assert_has_calls(
            [
                call(user_id=self.user.pk),
                call(user_id=self.owner.pk),
            ],
            any_order=True,
        )
