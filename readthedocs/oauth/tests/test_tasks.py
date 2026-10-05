from unittest import mock

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.integrations.models import GitLabWebhook
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAccountType
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.notifications import MESSAGE_OAUTH_UNSUPPORTED_GIT_PROVIDER
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_INTEGRATION_MISMATCH
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS
from readthedocs.oauth.services import GitHubService
from readthedocs.oauth.tasks import attach_webhook
from readthedocs.projects.models import Project


class AttachWebhookTests(TestCase):
    """Tests for the ``attach_webhook`` task.

    This task is the core of the GHSA-843j-p445-9532 security fix: a webhook
    must be attached using the accounts of the user making the request, never by
    brute forcing every account that has access to the project.
    """

    def setUp(self):
        self.user = get(User)
        self.project = get(
            Project,
            slug="project",
            repo="https://github.com/readthedocs/readthedocs.org",
            users=[self.user],
        )
        self.social_account = get(
            SocialAccount,
            user=self.user,
            provider=GitHubProvider.id,
        )
        get(SocialToken, account=self.social_account)

    def _project_notifications(self, message_id):
        return Notification.objects.filter(
            attached_to_id=self.project.pk,
            message_id=message_id,
        )

    @mock.patch.object(GitHubService, "for_project")
    @mock.patch.object(GitHubService, "for_user")
    def test_uses_requesting_user_accounts(self, for_user, for_project):
        """The webhook is set up with the services of the requesting user."""
        service = mock.Mock()
        service.setup_webhook.return_value = True
        for_user.return_value = [service]

        success = attach_webhook(project_pk=self.project.pk, user_pk=self.user.pk)

        assert success is True
        for_user.assert_called_once_with(self.user)
        for_project.assert_not_called()
        service.setup_webhook.assert_called_once_with(self.project, integration=None)
        self.project.refresh_from_db()
        assert self.project.has_valid_webhook is True

    def test_does_not_use_other_users_accounts(self):
        """A user can't attach a webhook using another user's account.

        The requesting user has no connected account, but another admin of the
        project does. The task must not fall back to the other user's account.
        """
        other_user = get(User)
        self.project.users.add(other_user)
        other_account = get(
            SocialAccount,
            user=other_user,
            provider=GitHubProvider.id,
        )
        get(SocialToken, account=other_account)

        requesting_user = get(User)
        self.project.users.add(requesting_user)

        with mock.patch.object(GitHubService, "setup_webhook") as setup_webhook:
            success = attach_webhook(
                project_pk=self.project.pk, user_pk=requesting_user.pk
            )

        assert success is False
        setup_webhook.assert_not_called()
        assert self._project_notifications(MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT).exists()
        self.project.refresh_from_db()
        assert self.project.has_valid_webhook is False

    def test_unknown_project_returns_false(self):
        assert attach_webhook(project_pk=9999999, user_pk=self.user.pk) is False

    def test_github_app_project_returns_true(self):
        """GitHub App projects don't need a webhook attached."""
        installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )
        self.project.remote_repository = get(
            RemoteRepository,
            remote_id="1234",
            full_name="user/repo",
            vcs_provider=GITHUB_APP,
            github_app_installation=installation,
        )
        self.project.save()

        with mock.patch.object(GitHubService, "setup_webhook") as setup_webhook:
            success = attach_webhook(
                project_pk=self.project.pk, user_pk=self.user.pk
            )

        assert success is True
        setup_webhook.assert_not_called()

    def test_unsupported_git_provider_adds_notification(self):
        self.project.repo = "https://example.com/user/repo"
        self.project.save()

        success = attach_webhook(project_pk=self.project.pk, user_pk=self.user.pk)

        assert success is False
        assert self._project_notifications(
            MESSAGE_OAUTH_UNSUPPORTED_GIT_PROVIDER
        ).exists()

    def test_no_account_adds_notification(self):
        """A user without a connected account gets the no-account notification."""
        user_without_account = get(User)
        self.project.users.add(user_without_account)

        success = attach_webhook(
            project_pk=self.project.pk, user_pk=user_without_account.pk
        )

        assert success is False
        assert self._project_notifications(MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT).exists()

    def test_integration_provider_mismatch_returns_false(self):
        """An integration incompatible with the project's provider is rejected."""
        # The project's repository is on GitHub, but the integration is for GitLab.
        integration = get(
            GitLabWebhook,
            project=self.project,
            integration_type=GitLabWebhook.integration_type_id,
        )

        with mock.patch.object(GitHubService, "setup_webhook") as setup_webhook:
            success = attach_webhook(
                project_pk=self.project.pk,
                user_pk=self.user.pk,
                integration=integration,
            )

        assert success is False
        setup_webhook.assert_not_called()
        assert self._project_notifications(
            MESSAGE_OAUTH_WEBHOOK_INTEGRATION_MISMATCH
        ).exists()

    @mock.patch.object(GitHubService, "for_user")
    def test_no_permissions_adds_notification(self, for_user):
        """The no-permissions notification is shown when the webhook setup fails."""
        service = mock.Mock()
        service.setup_webhook.return_value = False
        for_user.return_value = [service]

        success = attach_webhook(project_pk=self.project.pk, user_pk=self.user.pk)

        assert success is False
        assert self._project_notifications(
            MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS
        ).exists()
