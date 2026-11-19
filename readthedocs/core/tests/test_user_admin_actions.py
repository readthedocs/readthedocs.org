from unittest.mock import patch

import django_dynamic_fixture as fixture
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django import urls
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import TestCase


class UserAdminActionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fixture.get(User)
        cls.admin = fixture.get(User, is_staff=True, is_superuser=True)

    def setUp(self):
        self.client.force_login(self.admin)

    @patch("readthedocs.core.admin.sync_remote_repositories")
    def test_sync_remote_repositories_action(self, mock_sync_remote_repositories):
        action_data = {
            ACTION_CHECKBOX_NAME: [self.user.pk],
            "action": "sync_remote_repositories_action",
            "index": 0,
        }
        self.client.post(
            urls.reverse("admin:auth_user_changelist"),
            action_data,
        )
        mock_sync_remote_repositories.delay.assert_called_once_with(
            user_id=self.user.pk
        )


class UserAdminInlinesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = fixture.get(User)
        cls.admin = fixture.get(User, is_staff=True, is_superuser=True)
        cls.social_account = fixture.get(
            SocialAccount,
            user=cls.user,
            provider="github",
            uid="12345",
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_social_accounts_are_listed_on_user_change_page(self):
        response = self.client.get(
            urls.reverse("admin:auth_user_change", args=[self.user.pk]),
        )
        assert response.status_code == 200
        assert "Social accounts" in response.content.decode()
        assert self.social_account.uid in response.content.decode()

    def test_email_addresses_are_listed_on_user_change_page(self):
        email = fixture.get(EmailAddress, user=self.user, email="user@example.com", verified=True)
        response = self.client.get(
            urls.reverse("admin:auth_user_change", args=[self.user.pk]),
        )
        assert response.status_code == 200
        assert "Email addresses" in response.content.decode()
        assert email.email in response.content.decode()
