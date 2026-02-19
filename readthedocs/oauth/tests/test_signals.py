from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.oauth.notifications import MESSAGE_OAUTH_SYNCING_REMOTE_REPOSITORIES
from readthedocs.oauth.signals import _sync_remote_repositories
from readthedocs.projects import constants
from readthedocs.projects.models import Project


@patch("readthedocs.oauth.signals.sync_remote_repositories")
class TestSyncRemoteRepositoriesSignal(TestCase):
    def setUp(self):
        self.user = get(User, email="test@example.com")
        self.user.set_password("password")
        self.user.save()
        get(
            EmailAddress,
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )

    def _get_user_notifications(self):
        return Notification.objects.for_user(self.user, self.user).filter(
            message_id=MESSAGE_OAUTH_SYNCING_REMOTE_REPOSITORIES,
        )

    def test_no_social_account_no_notification_no_sync(self, mock_sync):
        """No notification or sync when user has no social account."""
        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_not_called()
        self.assertFalse(self._get_user_notifications().exists())

    def test_notification_shown_when_no_remote_repos(self, mock_sync):
        """Notification is shown when user has social account but no remote repositories."""
        get(SocialAccount, user=self.user, provider=GitHubAppProvider.id)

        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notifications().exists())

    def test_notification_shown_when_no_projects(self, mock_sync):
        """Notification is shown when user has remote repos but no access to any projects."""
        social_account = get(SocialAccount, user=self.user, provider=GitHubAppProvider.id)
        remote_repo = get(RemoteRepository)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=social_account,
        )

        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notifications().exists())

    def test_no_notification_when_user_has_repos_and_projects(self, mock_sync):
        """No notification when user has remote repos and access to projects."""
        social_account = get(SocialAccount, user=self.user, provider=GitHubAppProvider.id)
        remote_repo = get(RemoteRepository)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=social_account,
        )
        get(Project, users=[self.user], privacy_level=constants.PUBLIC)

        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertFalse(self._get_user_notifications().exists())

    def test_notification_created_on_login_when_no_remote_repos(self, mock_sync):
        """Notification is created when a user with no remote repos signs in."""
        get(SocialAccount, user=self.user, provider=GitHubAppProvider.id)

        self.client.post(
            reverse("account_login"),
            data={"login": self.user.username, "password": "password"},
        )

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notifications().exists())

    def test_no_notification_on_login_when_user_has_repos_and_projects(self, mock_sync):
        """No notification when a user with remote repos and projects signs in."""
        social_account = get(SocialAccount, user=self.user, provider=GitHubAppProvider.id)
        remote_repo = get(RemoteRepository)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=social_account,
        )
        get(Project, users=[self.user], privacy_level=constants.PUBLIC)

        self.client.post(
            reverse("account_login"),
            data={"login": self.user.username, "password": "password"},
        )

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertFalse(self._get_user_notifications().exists())
