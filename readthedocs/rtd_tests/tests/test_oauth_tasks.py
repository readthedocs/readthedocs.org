from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter,
)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.builds.models import Version
from readthedocs.oauth.constants import BITBUCKET, GITHUB, GITHUB_APP, GITLAB
from readthedocs.oauth.models import GitHubAccountType, GitHubAppInstallation, RemoteRepository
from readthedocs.oauth.services.github import GitHubService
from readthedocs.oauth.services.githubapp import GitHubAppService
from readthedocs.oauth.services.gitlab import GitLabService
from readthedocs.oauth.services.bitbucket import BitbucketService
from readthedocs.oauth.services.base import SyncServiceError
from readthedocs.oauth.tasks import (
    sync_remote_repositories,
    sync_remote_repositories_from_sso_organizations,
)
from readthedocs.organizations.models import Organization, OrganizationOwner
from readthedocs.projects.models import Project
from readthedocs.sso.models import SSOIntegration


class SyncRemoteRepositoriesTests(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.version = get(Version, project=self.project)
        self.socialaccount_gh = get(
            SocialAccount,
            user=self.user,
            provider=GitHubOAuth2Adapter.provider_id,
        )
        self.socialaccount_ghapp = get(
            SocialAccount,
            user=self.user,
            provider=GitHubAppProvider.id,
        )
        self.socialaccount_gl = get(
            SocialAccount,
            user=self.user,
            provider=GitLabOAuth2Adapter.provider_id,
        )
        self.socialaccount_bb = get(
            SocialAccount,
            user=self.user,
            provider=BitbucketOAuth2Adapter.provider_id,
        )

    @patch("readthedocs.oauth.services.githubapp.GitHubAppService.sync_user_access")
    @patch("readthedocs.oauth.services.github.GitHubService.sync")
    @patch("readthedocs.oauth.services.gitlab.GitLabService.sync")
    @patch("readthedocs.oauth.services.bitbucket.BitbucketService.sync")
    def test_sync_repository(self, sync_bb, sync_gl, sync_gh, sync_ghapp):
        r = sync_remote_repositories(self.user.pk)
        self.assertNotIn("error", r)
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()
        sync_ghapp.assert_called_once()

    @patch("readthedocs.oauth.services.githubapp.GitHubAppService.sync_user_access")
    @patch("readthedocs.oauth.services.github.GitHubService.sync")
    @patch("readthedocs.oauth.services.gitlab.GitLabService.sync")
    @patch("readthedocs.oauth.services.bitbucket.BitbucketService.sync")
    def test_sync_repository_failsync(self, sync_bb, sync_gl, sync_gh, sync_ghapp):
        sync_gh.side_effect = SyncServiceError
        r = sync_remote_repositories(self.user.pk)
        self.assertIn("GitHub", r["error"])
        self.assertNotIn("GitLab", r["error"])
        self.assertNotIn("Bitbucket", r["error"])
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()
        sync_ghapp.assert_called_once()

    @patch("readthedocs.oauth.services.githubapp.GitHubAppService.sync_user_access")
    @patch("readthedocs.oauth.services.github.GitHubService.sync")
    @patch("readthedocs.oauth.services.gitlab.GitLabService.sync")
    @patch("readthedocs.oauth.services.bitbucket.BitbucketService.sync")
    def test_sync_repository_failsync_more_than_one(
        self, sync_bb, sync_gl, sync_gh, sync_ghapp
    ):
        sync_gh.side_effect = SyncServiceError
        sync_bb.side_effect = SyncServiceError
        r = sync_remote_repositories(self.user.pk)
        self.assertIn("GitHub", r["error"])
        self.assertIn("Bitbucket", r["error"])
        self.assertNotIn("GitLab", r["error"])
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()
        sync_ghapp.assert_called_once()

    @patch.object(GitHubService, "update_repository")
    @patch.object(GitHubAppService, "update_repository")
    @patch.object(GitLabService, "update_repository")
    @patch.object(BitbucketService, "update_repository")
    def test_sync_remote_repository_organizations_without_slugs(
        self, update_repository_bb, update_repository_gl, update_repository_ghapp, update_repository_gh
    ):
        organization = get(Organization)
        get(
            SSOIntegration,
            provider=SSOIntegration.PROVIDER_ALLAUTH,
            organization=organization,
        )
        get(
            OrganizationOwner,
            owner=self.user,
            organization=organization,
        )

        gh_repository = get(
            RemoteRepository,
            full_name="org/repo",
            vcs_provider=GITHUB,
        )
        gh_repository.get_remote_repository_relation(self.user, self.socialaccount_gh)

        ghapp_installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )
        ghapp_repository = get(
            RemoteRepository,
            full_name="org/repo",
            vcs_provider=GITHUB_APP,
            github_app_installation=ghapp_installation,
        )
        ghapp_repository.get_remote_repository_relation(self.user, self.socialaccount_ghapp)

        gl_repository = get(
            RemoteRepository,
            full_name="org/repo",
            vcs_provider=GITLAB,
        )
        gl_repository.get_remote_repository_relation(self.user, self.socialaccount_gl)

        bb_repository = get(
            RemoteRepository,
            full_name="org/repo",
            vcs_provider=BITBUCKET,
        )
        bb_repository.get_remote_repository_relation(self.user, self.socialaccount_bb)

        remote_repositories = [
            gh_repository,
            ghapp_repository,
            gl_repository,
            bb_repository,
        ]
        for remote_repository in remote_repositories:
            project = get(Project, remote_repository=remote_repository)
            organization.projects.add(project)

        sync_remote_repositories_from_sso_organizations()

        update_repository_gh.assert_called_once_with(gh_repository)
        update_repository_gl.assert_called_once_with(gl_repository)
        update_repository_bb.assert_called_once_with(bb_repository)
        update_repository_ghapp.assert_not_called()


    @patch("readthedocs.oauth.services.githubapp.GitHubAppService.sync_user_access")
    @patch("readthedocs.oauth.services.github.GitHubService.sync")
    @patch("readthedocs.oauth.services.gitlab.GitLabService.sync")
    @patch("readthedocs.oauth.services.bitbucket.BitbucketService.sync")
    def test_sync_dont_stop_if_one_service_account_of_same_type_fails(
        self, sync_bb, sync_gl, sync_gh, sync_ghapp
    ):
        get(
            SocialAccount,
            user=self.user,
            provider=GitHubOAuth2Adapter.provider_id,
        )
        sync_gh.side_effect = SyncServiceError
        r = sync_remote_repositories(self.user.pk)
        assert "GitHub" in r["error"]
        assert "Bitbucket" not in r["error"]
        assert "GitLab" not in r["error"]
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_ghapp.assert_called_once()
        assert sync_gh.call_count == 2
