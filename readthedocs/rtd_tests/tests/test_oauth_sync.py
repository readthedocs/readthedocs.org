from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
import django_dynamic_fixture as fixture
import requests_mock

from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.oauth.services import (
    GitHubService,
)
from readthedocs.projects.models import Project


class GitHubOAuthSyncTests(TestCase):
    payload_user_repos = [{
        'id': 11111,
        'node_id': 'a1b2c3',
        'name': 'repository',
        'full_name': 'organization/repository',
        'private': False,
        'owner': {
            'login': 'organization',
            'id': 11111,
            'node_id': 'a1b2c3',
            'avatar_url': 'https://avatars3.githubusercontent.com/u/11111?v=4',
            'gravatar_id': '',
            'url': 'https://api.github.com/users/organization',
            'type': 'User',
            'site_admin': False,
        },
        'html_url': 'https://github.com/organization/repository',
        'description': '',
        'fork': True,
        'url': 'https://api.github.com/repos/organization/repository',
        'created_at': '2019-06-14T14:11:29Z',
        'updated_at': '2019-06-15T15:05:33Z',
        'pushed_at': '2019-06-15T15:11:19Z',
        'git_url': 'git://github.com/organization/repository.git',
        'ssh_url': 'git@github.com:organization/repository.git',
        'clone_url': 'https://github.com/organization/repository.git',
        'svn_url': 'https://github.com/organization/repository',
        'homepage': None,
        'language': 'Python',
        'archived': False,
        'disabled': False,
        'open_issues_count': 0,
        'default_branch': 'master',
        'permissions': {
            'admin': False,
            'push': True,
            'pull': True,
        },
    }]

    def setUp(self):
        self.user = fixture.get(User)
        self.socialaccount = fixture.get(
            SocialAccount,
            user=self.user,
            provider=GitHubOAuth2Adapter.provider_id,
        )
        self.token = fixture.get(
            SocialToken,
            account=self.socialaccount,
        )
        self.service = GitHubService.for_user(self.user)[0]

    @requests_mock.Mocker(kw='mock_request')
    def test_sync_delete_stale(self, mock_request):
        mock_request.get('https://api.github.com/user/repos', json=self.payload_user_repos)
        mock_request.get('https://api.github.com/user/orgs', json=[])

        repo_1 = fixture.get(
            RemoteRepository,
            full_name='organization/repository',
            remote_id='11111',
            vcs_provider=GITHUB
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_1,
            user=self.user,
            account=self.socialaccount
        )

        repo_2 = fixture.get(
            RemoteRepository,
            full_name='organization/old-repository',
            remote_id='64789',
            vcs_provider=GITHUB
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_2,
            user=self.user,
            account=self.socialaccount
        )

        # RemoteRepositoryRelation with RemoteRepository
        # linked to a Project should also be removed
        project = fixture.get(Project)
        repo_3 = fixture.get(
            RemoteRepository,
            project=project,
            full_name='organization/project-linked-repository',
            remote_id='54321',
            vcs_provider=GITHUB
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_3,
            user=self.user,
            account=self.socialaccount
        )

        org = fixture.get(
            RemoteOrganization,
            name='organization',
        )
        fixture.get(
            RemoteOrganizationRelation,
            remote_organization=org,
            user=self.user,
            account=self.socialaccount
        )

        self.assertEqual(RemoteRepository.objects.count(), 3)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 3)
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 1)

        self.service.sync()

        # After calling .sync, old-repository remote relation should be deleted,
        # project-linked-repository remote relation should be conserved,
        # and only the one's returned by the API should be present (organization/repository)
        self.assertEqual(RemoteRepository.objects.count(), 3)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)
        self.assertTrue(RemoteRepository.objects.filter(full_name='organization/repository').exists())
        self.assertTrue(RemoteRepository.objects.filter(full_name='organization/project-linked-repository').exists())
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 0)

    @requests_mock.Mocker(kw='mock_request')
    def test_sync_repositories(self, mock_request):
        mock_request.get('https://api.github.com/user/repos', json=self.payload_user_repos)

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)

        remote_repositories = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(RemoteOrganization.objects.count(), 0)
        self.assertEqual(len(remote_repositories), 1)
        remote_repository = remote_repositories[0]
        self.assertIsInstance(remote_repository, RemoteRepository)
        self.assertEqual(remote_repository.full_name, 'organization/repository')
        self.assertEqual(remote_repository.name, 'repository')
        self.assertFalse(remote_repository.remote_repository_relations.first().admin)
        self.assertFalse(remote_repository.private)

    @requests_mock.Mocker(kw='mock_request')
    def test_sync_repositories_only_creates_one_remote_repo_per_vcs_repo(self, mock_request):
        mock_request.get('https://api.github.com/user/repos', json=self.payload_user_repos)

        self.assertEqual(RemoteRepository.objects.count(), 0)

        remote_repositories = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(len(remote_repositories), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)

        user_2 = fixture.get(User)
        user_2_socialaccount = fixture.get(
            SocialAccount,
            user=user_2,
            provider=GitHubOAuth2Adapter.provider_id,
        )
        fixture.get(
            SocialToken,
            account=user_2_socialaccount,
        )

        service_2 = GitHubService(user=user_2, account=user_2_socialaccount)
        remote_repositories = service_2.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(len(remote_repositories), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 2)

    @requests_mock.Mocker(kw='mock_request')
    def test_sync_organizations(self, mock_request):
        payload = [{
            'login': 'readthedocs',
            'id': 11111,
            'node_id': 'a1b2c3',
            'url': 'https://api.github.com/orgs/organization',
            'avatar_url': 'https://avatars2.githubusercontent.com/u/11111?v=4',
            'description': ''
        }]
        mock_request.get('https://api.github.com/user/orgs', json=payload)

        payload = {
           'login': 'organization',
            'id': 11111,
            'node_id': 'a1b2c3',
            'url': 'https://api.github.com/orgs/organization',
            'avatar_url': 'https://avatars2.githubusercontent.com/u/11111?v=4',
            'description': '',
            'name': 'Organization',
            'company': None,
            'blog': 'http://organization.org',
            'location': 'Portland, Oregon & Worldwide. ',
            'email': None,
            'is_verified': False,
            'html_url': 'https://github.com/organization',
            'created_at': '2010-08-16T19:17:46Z',
            'updated_at': '2020-08-12T14:26:39Z',
            'type': 'Organization',
        }
        mock_request.get('https://api.github.com/orgs/organization', json=payload)

        payload = [{
            'id': 11111,
            'node_id': 'a1b2c3',
            'name': 'repository',
            'full_name': 'organization/repository',
            'private': False,
            'owner': {
                'login': 'organization',
                'id': 11111,
                'node_id': 'a1b2c3',
                'avatar_url': 'https://avatars3.githubusercontent.com/u/11111?v=4',
                'gravatar_id': '',
                'url': 'https://api.github.com/users/organization',
                'type': 'User',
                'site_admin': False,
            },
            'html_url': 'https://github.com/organization/repository',
            'description': '',
            'fork': True,
            'url': 'https://api.github.com/repos/organization/repository',
            'created_at': '2019-06-14T14:11:29Z',
            'updated_at': '2019-06-15T15:05:33Z',
            'pushed_at': '2019-06-15T15:11:19Z',
            'git_url': 'git://github.com/organization/repository.git',
            'ssh_url': 'git@github.com:organization/repository.git',
            'clone_url': 'https://github.com/organization/repository.git',
            'svn_url': 'https://github.com/organization/repository',
            'homepage': None,
            'language': 'Python',
            'archived': False,
            'disabled': False,
            'open_issues_count': 0,
            'default_branch': 'master',
            'permissions': {
                'admin': False,
                'push': True,
                'pull': True,
            },
        }]
        mock_request.get('https://api.github.com/orgs/organization/repos', json=payload)

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 0)

        remote_organizations, remote_repositories = self.service.sync_organizations()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 1)
        self.assertEqual(len(remote_organizations), 1)
        self.assertEqual(len(remote_repositories), 1)
        remote_organization = remote_organizations[0]
        self.assertIsInstance(remote_organization, RemoteOrganization)
        self.assertEqual(remote_organization.name, 'Organization')
