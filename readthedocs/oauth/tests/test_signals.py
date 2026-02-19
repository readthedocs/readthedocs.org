from unittest.mock import patch

from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django_dynamic_fixture import get

from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.oauth.notifications import MESSAGE_OAUTH_SYNCING_REMOTE_REPOSITORIES
from readthedocs.oauth.signals import _sync_remote_repositories
from readthedocs.projects import constants
from readthedocs.projects.models import Project


@patch("readthedocs.oauth.signals.sync_remote_repositories")
class TestSyncRemoteRepositoriesSignal(TestCase):
    def setUp(self):
        self.user = get(User)

    def _get_user_notification(self):
        return Notification.objects.filter(
            attached_to_content_type=ContentType.objects.get_for_model(self.user),
            attached_to_id=self.user.pk,
            message_id=MESSAGE_OAUTH_SYNCING_REMOTE_REPOSITORIES,
        )

    def test_no_social_account_no_notification_no_sync(self, mock_sync):
        """No notification or sync when user has no social account."""
        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_not_called()
        self.assertFalse(self._get_user_notification().exists())

    def test_notification_shown_when_no_remote_repos(self, mock_sync):
        """Notification is shown when user has social account but no remote repositories."""
        get(SocialAccount, user=self.user, provider=GitHubOAuth2Adapter.provider_id)

        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notification().exists())

    def test_notification_shown_when_no_projects(self, mock_sync):
        """Notification is shown when user has remote repos but no access to any projects."""
        social_account = get(
            SocialAccount, user=self.user, provider=GitHubOAuth2Adapter.provider_id
        )
        remote_repo = get(RemoteRepository)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=social_account,
        )

        _sync_remote_repositories(self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notification().exists())

    def test_no_notification_when_user_has_repos_and_projects(self, mock_sync):
        """No notification when user has remote repos and access to projects."""
        social_account = get(
            SocialAccount, user=self.user, provider=GitHubOAuth2Adapter.provider_id
        )
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
        self.assertFalse(self._get_user_notification().exists())

    def test_notification_created_on_login_when_no_remote_repos(self, mock_sync):
        """Notification is created when a user with no remote repos signs in."""
        get(SocialAccount, user=self.user, provider=GitHubOAuth2Adapter.provider_id)
        request = RequestFactory().get("/")

        user_logged_in.send(sender=User, request=request, user=self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertTrue(self._get_user_notification().exists())

    def test_no_notification_on_login_when_user_has_repos_and_projects(self, mock_sync):
        """No notification when a user with remote repos and projects signs in."""
        social_account = get(
            SocialAccount, user=self.user, provider=GitHubOAuth2Adapter.provider_id
        )
        remote_repo = get(RemoteRepository)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=social_account,
        )
        get(Project, users=[self.user], privacy_level=constants.PUBLIC)
        request = RequestFactory().get("/")

        user_logged_in.send(sender=User, request=request, user=self.user)

        mock_sync.delay.assert_called_once_with(self.user.pk)
        self.assertFalse(self._get_user_notification().exists())
