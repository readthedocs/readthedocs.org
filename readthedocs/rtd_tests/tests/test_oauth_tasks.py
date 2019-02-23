from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter,
)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from mock import patch

from readthedocs.builds.models import Version
from readthedocs.oauth.services.base import SyncServiceError
from readthedocs.oauth.tasks import sync_remote_repositories
from readthedocs.projects.models import Project


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

    @patch('readthedocs.oauth.services.github.GitHubService.sync')
    @patch('readthedocs.oauth.services.gitlab.GitLabService.sync')
    @patch('readthedocs.oauth.services.bitbucket.BitbucketService.sync')
    def test_sync_repository(self, sync_bb, sync_gl, sync_gh):
        r = sync_remote_repositories(self.user.pk)
        self.assertNotIn('error', r)
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()

    @patch('readthedocs.oauth.services.github.GitHubService.sync')
    @patch('readthedocs.oauth.services.gitlab.GitLabService.sync')
    @patch('readthedocs.oauth.services.bitbucket.BitbucketService.sync')
    def test_sync_repository_failsync(self, sync_bb, sync_gl, sync_gh):
        sync_gh.side_effect = SyncServiceError
        r = sync_remote_repositories(self.user.pk)
        self.assertIn('GitHub', r['error'])
        self.assertNotIn('GitLab', r['error'])
        self.assertNotIn('Bitbucket', r['error'])
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()

    @patch('readthedocs.oauth.services.github.GitHubService.sync')
    @patch('readthedocs.oauth.services.gitlab.GitLabService.sync')
    @patch('readthedocs.oauth.services.bitbucket.BitbucketService.sync')
    def test_sync_repository_failsync_more_than_one(self, sync_bb, sync_gl, sync_gh):
        sync_gh.side_effect = SyncServiceError
        sync_bb.side_effect = SyncServiceError
        r = sync_remote_repositories(self.user.pk)
        self.assertIn('GitHub', r['error'])
        self.assertIn('Bitbucket', r['error'])
        self.assertNotIn('GitLab', r['error'])
        sync_bb.assert_called_once()
        sync_gl.assert_called_once()
        sync_gh.assert_called_once()
