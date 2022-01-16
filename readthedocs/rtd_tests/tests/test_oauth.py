from unittest import mock

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATUS_SUCCESS, EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.integrations.models import GitHubWebhook, GitLabWebhook
from readthedocs.oauth.constants import BITBUCKET, GITHUB, GITLAB
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.oauth.services import (
    BitbucketService,
    GitHubService,
    GitLabService,
)
from readthedocs.projects import constants
from readthedocs.projects.models import Project


class GitHubOAuthTests(TestCase):

    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.org = RemoteOrganization.objects.create(slug='rtfd')
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.service = GitHubService(
            user=self.user,
            account=get(SocialAccount, user=self.user)
        )
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build, project=self.project, version=self.external_version, commit='1234',
        )
        self.integration = get(
            GitHubWebhook,
            project=self.project,
            provider_data={
                'url': 'https://github.com/'
            }
        )
        self.provider_data = [
            {
                "config": {
                    "url": "https://example.com/webhook"
                },
                "url": "https://api.github.com/repos/test/Hello-World/hooks/12345678",
            }
        ]

    def test_make_project_pass(self):
        repo_json = {
            'name': 'testrepo',
            'full_name': 'testuser/testrepo',
            'id': '12345678',
            'description': 'Test Repo',
            'git_url': 'git://github.com/testuser/testrepo.git',
            'private': False,
            'ssh_url': 'ssh://git@github.com:testuser/testrepo.git',
            'html_url': 'https://github.com/testuser/testrepo',
            'clone_url': 'https://github.com/testuser/testrepo.git',
        }
        repo = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, 'testrepo')
        self.assertEqual(repo.full_name, 'testuser/testrepo')
        self.assertEqual(repo.remote_id, '12345678')
        self.assertEqual(repo.vcs_provider, GITHUB)
        self.assertEqual(repo.description, 'Test Repo')
        self.assertEqual(
            repo.avatar_url,
            settings.OAUTH_AVATAR_USER_DEFAULT_URL,
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url, 'https://github.com/testuser/testrepo.git',
        )
        self.assertEqual(
            repo.ssh_url, 'ssh://git@github.com:testuser/testrepo.git',
        )
        self.assertEqual(repo.html_url, 'https://github.com/testuser/testrepo')

    def test_make_project_fail(self):
        repo_json = {
            'name': '',
            'full_name': '',
            'id': '',
            'description': '',
            'git_url': '',
            'private': True,
            'ssh_url': '',
            'html_url': '',
            'clone_url': '',
        }
        github_project = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        self.assertIsNone(github_project)

    def test_make_organization(self):
        org_json = {
            'id': 12345,
            'html_url': 'https://github.com/testorg',
            'name': 'Test Org',
            'email': 'test@testorg.org',
            'login': 'testorg',
            'avatar_url': 'https://images.github.com/foobar',
        }
        org = self.service.create_organization(org_json)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, 'testorg')
        self.assertEqual(org.name, 'Test Org')
        self.assertEqual(org.email, 'test@testorg.org')
        self.assertEqual(org.avatar_url, 'https://images.github.com/foobar')
        self.assertEqual(org.url, 'https://github.com/testorg')

    def test_import_with_no_token(self):
        """User without a GitHub SocialToken does not return a service."""
        services = GitHubService.for_user(get(User))
        self.assertEqual(services, [])

    def test_multiple_users_same_repo(self):
        repo_json = {
            'name': '',
            'full_name': 'testrepo/multiple',
            'id': '12345678',
            'description': '',
            'git_url': '',
            'private': False,
            'ssh_url': '',
            'html_url': '',
            'clone_url': '',
        }

        github_project = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )

        user2 = User.objects.get(pk=2)
        service = GitHubService(
            user=user2,
            account=get(SocialAccount, user=self.user)
        )
        github_project_2 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        self.assertIsInstance(github_project, RemoteRepository)
        self.assertIsInstance(github_project_2, RemoteRepository)
        self.assertEqual(github_project_2, github_project)

        github_project_3 = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        github_project_4 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        self.assertIsInstance(github_project_3, RemoteRepository)
        self.assertIsInstance(github_project_4, RemoteRepository)
        self.assertEqual(github_project, github_project_3)
        self.assertEqual(github_project_2, github_project_4)

        github_project_5 = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        github_project_6 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )

        self.assertEqual(github_project, github_project_5)
        self.assertEqual(github_project_2, github_project_6)

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_send_build_status_successful(self, session, mock_logger):
        session().post.return_value.status_code = 201
        success = self.service.send_build_status(
            self.external_build,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS
        )

        self.assertTrue(success)
        mock_logger.bind.assert_called_with(http_status_code=201)
        mock_logger.info.assert_called_with(
            "GitHub commit status created for project.",
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_send_build_status_404_error(self, session, mock_logger):
        session().post.return_value.status_code = 404
        success = self.service.send_build_status(
            self.external_build,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.bind.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            'GitHub project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_send_build_status_value_error(self, session, mock_logger):
        session().post.side_effect = ValueError
        success = self.service.send_build_status(
            self.external_build, self.external_build.commit, BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            commit_status='success',
            user_username=self.user.username,
            statuses_url='https://api.github.com/repos/pypa/pip/statuses/1234',
        )
        mock_logger.exception.assert_called_with(
            'GitHub commit status creation failed for project.',
        )

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        repo_json = {
            'name': 'testrepo',
            'full_name': 'testuser/testrepo',
            'id': '12345678',
            'description': 'Test Repo',
            'git_url': 'git://github.com/testuser/testrepo.git',
            'private': False,
            'ssh_url': 'ssh://git@github.com:testuser/testrepo.git',
            'html_url': 'https://github.com/testuser/testrepo',
            'clone_url': 'https://github.com/testuser/testrepo.git',
        }
        repo = self.service.create_repository(repo_json, organization=self.org)
        self.assertIsNotNone(repo)

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_setup_webhook_successful(self, session, mock_logger):
        session().post.return_value.status_code = 201
        session().post.return_value.json.return_value = {}
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_logger.bind.assert_called_with(http_status_code=201)
        mock_logger.info.assert_called_with(
            "GitHub webhook creation successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_setup_webhook_404_error(self, session, mock_logger):
        session().post.return_value.status_code = 404
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )
        self.integration.refresh_from_db()

        self.assertFalse(success)
        self.assertIsNone(self.integration.secret)
        mock_logger.bind.assert_called_with(http_status_code=404)
        mock_logger.warning.assert_called_with(
            'GitHub project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_setup_webhook_value_error(self, session, mock_logger):
        session().post.side_effect = ValueError
        success = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertIsNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.github.com/repos/pypa/pip/hooks',
        )
        mock_logger.exception.assert_called_with(
            'GitHub webhook creation failed for project.',
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_update_webhook_successful(self, session, mock_logger):
        session().patch.return_value.status_code = 201
        session().patch.return_value.json.return_value = {}
        success, _ = self.service.update_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            http_status_code=201,
            url='https://github.com/',
        )
        mock_logger.info.assert_called_with(
            "GitHub webhook update successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.setup_webhook')
    def test_update_webhook_404_error(self, setup_webhook, session):
        session().patch.return_value.status_code = 404
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.setup_webhook')
    def test_update_webhook_no_provider_data(self, setup_webhook, session):
        self.integration.provider_data = None
        self.integration.save()

        session().patch.side_effect = AttributeError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_update_webhook_value_error(self, session, mock_logger):
        session().patch.side_effect = ValueError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertIsNone(self.integration.secret)
        mock_logger.exception.assert_called_with('GitHub webhook update failed for project.')

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_get_provider_data_successful(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = 'https://{domain}{path}'.format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                'api_webhook',
                kwargs={
                    'project_slug': self.project.slug,
                    'integration_pk': self.integration.pk,
                },
            )
        )
        webhook_data[0]["config"]["url"] = rtd_webhook_url

        session().get.return_value.status_code = 200
        session().get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data[0])
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.github.com/repos/pypa/pip/hooks',
        )
        mock_logger.info.assert_called_with(
            'GitHub integration updated with provider data for project.',
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_get_provider_data_404_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.return_value.status_code = 404

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.warning.assert_called_with(
            'GitHub project does not exist or user does not have permissions.',
            https_status_code=404,
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_get_provider_data_attribute_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.side_effect = AttributeError

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.github.com/repos/pypa/pip/hooks',
        )
        mock_logger.exception.assert_called_with(
            'GitHub webhook Listing failed for project.',
        )


class BitbucketOAuthTests(TestCase):

    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.project.repo = 'https://bitbucket.org/testuser/testrepo/'
        self.project.save()
        self.org = RemoteOrganization.objects.create(slug='rtfd')
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.service = BitbucketService(
            user=self.user,
            account=get(SocialAccount, user=self.user)
        )
        self.integration = get(
            GitHubWebhook,
            project=self.project,
            provider_data={
                'links': {
                    'self': {
                        'href': 'https://bitbucket.org/'
                    }
                }
            }
        )
        self.provider_data = {
            'values': [{
                'links': {
                    'self': {
                        'href': 'https://bitbucket.org/'
                    }
                },
                'url': 'https://readthedocs.io/api/v2/webhook/test/99999999/',
            },]
        }
        self.repo_response_data = {
            'scm': 'hg',
            'has_wiki': True,
            'description': 'Site for tutorial101 files',
            'links': {
                'watchers': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/watchers',
                },
                'commits': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/commits',
                },
                'self': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org',
                },
                'html': {
                    'href': 'https://bitbucket.org/tutorials/tutorials.bitbucket.org',
                },
                'avatar': {
                    'href': 'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/tutorials.bitbucket.org-logo-1456883302-9_avatar.png',
                },
                'forks': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/forks',
                },
                'clone': [
                    {
                        'href': 'https://tutorials@bitbucket.org/tutorials/tutorials.bitbucket.org',
                        'name': 'https',
                    },
                    {
                        'href': 'ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org',
                        'name': 'ssh',
                    },
                ],
                'pullrequests': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/pullrequests',
                },
            },
            'fork_policy': 'allow_forks',
            'name': 'tutorials.bitbucket.org',
            'language': 'html/css',
            'created_on': '2011-12-20T16:35:06.480042+00:00',
            'full_name': 'tutorials/tutorials.bitbucket.org',
            'has_issues': True,
            'owner': {
                'username': 'tutorials',
                'display_name': 'tutorials account',
                'uuid': '{c788b2da-b7a2-404c-9e26-d3f077557007}',
                'links': {
                    'self': {
                        'href': 'https://api.bitbucket.org/2.0/users/tutorials',
                    },
                    'html': {
                        'href': 'https://bitbucket.org/tutorials',
                    },
                    'avatar': {
                        'href': 'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2013/Nov/25/tutorials-avatar-1563784409-6_avatar.png',
                    },
                },
            },
            'updated_on': '2014-11-03T02:24:08.409995+00:00',
            'size': 76182262,
            'is_private': False,
            'uuid': '{9970a9b6-2d86-413f-8555-da8e1ac0e542}',
            'mainbranch': {
                'type': 'branch',
                'name': 'main',
            },
        }

        self.team_response_data = {
            'slug': 'teamsinspace',
            'name': 'Teams In Space',
            'uuid': '{61fc5cf6-d054-47d2-b4a9-061ccf858379}',
            'links': {
                'self': {
                    'href': 'https://api.bitbucket.org/2.0/workspaces/teamsinspace',
                },
                'repositories': {
                    'href': 'https://api.bitbucket.org/2.0/repositories/teamsinspace',
                },
                'html': {'href': 'https://bitbucket.org/teamsinspace'},
                'avatar': {
                    'href': 'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/teamsinspace-avatar-3731530358-7_avatar.png',
                },
                'members': {
                    'href': 'https://api.bitbucket.org/2.0/workspaces/teamsinspace/members',
                },
                'owners': {
                    'href': 'https://api.bitbucket.org/2.0/workspaces/teamsinspace/members?q=permission%3D%22owner%22',
                },
                'hooks': {
                    'href': 'https://api.bitbucket.org/2.0/workspaces/teamsinspace/hooks',
                },
                'snippets': {
                    'href': 'https://api.bitbucket.org/2.0/snippets/teamsinspace/',
                },
                'projects': {
                    'href': 'https://api.bitbucket.org/2.0/workspaces/teamsinspace/projects',
                },
            },
            'created_on': '2014-04-08T00:00:14.070969+00:00',
            'type': 'workspace',
            'is_private': True,
        }

    def test_make_project_pass(self):
        repo = self.service.create_repository(
            self.repo_response_data, organization=self.org,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, 'tutorials.bitbucket.org')
        self.assertEqual(repo.full_name, 'tutorials/tutorials.bitbucket.org')
        self.assertEqual(repo.remote_id, '{9970a9b6-2d86-413f-8555-da8e1ac0e542}')
        self.assertEqual(repo.vcs_provider, BITBUCKET)
        self.assertEqual(repo.description, 'Site for tutorial101 files')
        self.assertEqual(repo.default_branch, 'main')
        self.assertEqual(
            repo.avatar_url, (
                'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/'
                'tutorials.bitbucket.org-logo-1456883302-9_avatar.png'
            ),
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            'https://bitbucket.org/tutorials/tutorials.bitbucket.org',
        )
        self.assertEqual(
            repo.ssh_url,
            'ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org',
        )
        self.assertEqual(
            repo.html_url,
            'https://bitbucket.org/tutorials/tutorials.bitbucket.org',
        )

    def test_make_project_mainbranch_none(self):
        self.repo_response_data['mainbranch'] = None
        repo = self.service.create_repository(
            self.repo_response_data, organization=self.org,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, 'tutorials.bitbucket.org')
        self.assertEqual(repo.full_name, 'tutorials/tutorials.bitbucket.org')
        self.assertEqual(repo.description, 'Site for tutorial101 files')
        self.assertEqual(
            repo.avatar_url, (
                'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/'
                'tutorials.bitbucket.org-logo-1456883302-9_avatar.png'
            ),
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            'https://bitbucket.org/tutorials/tutorials.bitbucket.org',
        )
        self.assertEqual(
            repo.ssh_url,
            'ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org',
        )
        self.assertEqual(
            repo.html_url,
            'https://bitbucket.org/tutorials/tutorials.bitbucket.org',
        )
        self.assertEqual(repo.default_branch, None)

    def test_make_project_fail(self):
        data = self.repo_response_data.copy()
        data['is_private'] = True
        repo = self.service.create_repository(
            data, organization=self.org, privacy=self.privacy,
        )
        self.assertIsNone(repo)

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        data = self.repo_response_data.copy()
        data['is_private'] = False
        repo = self.service.create_repository(data, organization=self.org)
        self.assertIsNotNone(repo)

    def test_make_organization(self):
        org = self.service.create_organization(self.team_response_data)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, 'teamsinspace')
        self.assertEqual(org.name, 'Teams In Space')
        self.assertEqual(
            org.avatar_url, (
                'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/'
                'teamsinspace-avatar-3731530358-7_avatar.png'
            ),
        )
        self.assertEqual(org.url, 'https://bitbucket.org/teamsinspace')

    def test_import_with_no_token(self):
        """User without a Bitbucket SocialToken does not return a service."""
        services = BitbucketService.for_user(get(User))
        self.assertEqual(services, [])

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_setup_webhook_successful(self, session, mock_logger):
        session().post.return_value.status_code = 201
        session().post.return_value.json.return_value = {}
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.assertTrue(success)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.info.assert_called_with(
            "Bitbucket webhook creation successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_setup_webhook_404_error(self, session, mock_logger):
        session().post.return_value.status_code = 404
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.assertFalse(success)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.info.assert_called_with(
            'Bitbucket project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_setup_webhook_value_error(self, session, mock_logger):
        session().post.side_effect = ValueError
        success = self.service.setup_webhook(
            self.project,
            self.integration
        )

        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.exception.assert_called_with(
            'Bitbucket webhook creation failed for project.',
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_update_webhook_successful(self, session, mock_logger):
        session().put.return_value.status_code = 200
        session().put.return_value.json.return_value = {}
        success, _ = self.service.update_webhook(
            self.project,
            self.integration
        )

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_logger.bind.assert_called_with(project_slug=self.project.slug)
        mock_logger.info.assert_called_with(
            "Bitbucket webhook update successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.setup_webhook')
    def test_update_webhook_404_error(self, setup_webhook, session):
        session().put.return_value.status_code = 404
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.setup_webhook')
    def test_update_webhook_no_provider_data(self, setup_webhook, session):
        self.integration.provider_data = None
        self.integration.save()

        session().put.side_effect = AttributeError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_update_webhook_value_error(self, session, mock_logger):
        session().put.side_effect = ValueError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        mock_logger.bind.assert_called_with(project_slug=self.project.slug)
        mock_logger.exception.assert_called_with(
            'Bitbucket webhook update failed for project.',
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_get_provider_data_successful(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = 'https://{domain}{path}'.format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                'api_webhook',
                kwargs={
                    'project_slug': self.project.slug,
                    'integration_pk': self.integration.pk,
                },
            )
        )
        webhook_data['values'][0]["url"] = rtd_webhook_url

        session().get.return_value.status_code = 200
        session().get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data['values'][0])
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.info.assert_called_with(
            'Bitbucket integration updated with provider data for project.',
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_get_provider_data_404_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.return_value.status_code = 404

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.info.assert_called_with(
            'Bitbucket project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.bitbucket.log')
    @mock.patch('readthedocs.oauth.services.bitbucket.BitbucketService.get_session')
    def test_get_provider_data_attribute_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.side_effect = AttributeError

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks',
        )
        mock_logger.exception.assert_called_with(
            'Bitbucket webhook Listing failed for project.',
        )


class GitLabOAuthTests(TestCase):

    fixtures = ['eric', 'test_data']

    repo_response_data = {
        'lfs_enabled': True,
        'request_access_enabled': False,
        'approvals_before_merge': 0,
        'forks_count': 12,
        'only_allow_merge_if_all_discussions_are_resolved': False,
        'container_registry_enabled': True,
        'web_url': 'https://gitlab.com/testorga/testrepo',
        'owner': {
            'username': 'testorga',
            'web_url': 'https://gitlab.com/testorga',
            'name': 'Test Orga',
            'state': 'active',
            'avatar_url': 'https://secure.gravatar.com/avatar/test',
            'id': 42,
        },
        'wiki_enabled': True,
        'id': 42,
        'merge_requests_enabled': True,
        'archived': False,
        'snippets_enabled': True,
        'http_url_to_repo': 'https://gitlab.com/testorga/testrepo.git',
        'namespace': {
            'kind': 'user',
            'name': 'Test Orga',
            'parent_id': None,
            'plan': 'early_adopter',
            'path': 'testorga',
            'id': 42,
            'full_path': 'testorga',
        },
        'star_count': 1,
        '_links': {
            'repo_branches': 'http://gitlab.com/api/v4/projects/42/repository/branches',
            'merge_requests': 'http://gitlab.com/api/v4/projects/42/merge_requests',
            'self': 'http://gitlab.com/api/v4/projects/42',
            'labels': 'http://gitlab.com/api/v4/projects/42/labels',
            'members': 'http://gitlab.com/api/v4/projects/42/members',
            'events': 'http://gitlab.com/api/v4/projects/42/events',
            'issues': 'http://gitlab.com/api/v4/projects/42/issues',
        },
        'resolve_outdated_diff_discussions': False,
        'issues_enabled': True,
        'path_with_namespace': 'testorga/testrepo',
        'ci_config_path': None,
        'shared_with_groups': [],
        'description': 'Test Repo',
        'default_branch': 'master',
        'visibility': 'public',
        'ssh_url_to_repo': 'git@gitlab.com:testorga/testrepo.git',
        'public_jobs': True,
        'path': 'testrepo',
        'import_status': 'none',
        'only_allow_merge_if_pipeline_succeeds': False,
        'open_issues_count': 0,
        'last_activity_at': '2017-11-28T14:21:17.570Z',
        'name': 'testrepo',
        'printing_merge_request_link_enabled': True,
        'name_with_namespace': 'testorga / testrepo',
        'created_at': '2017-11-27T19:19:30.906Z',
        'shared_runners_enabled': True,
        'creator_id': 389803,
        'avatar_url': None,
        'permissions': {
            'group_access': None,
            'project_access': {
                'notification_level': 3,
                'access_level': 40,
            },
        },
        'tag_list': [],
        'jobs_enabled': True,
    }

    group_response_data = {
        'id': 1,
        'name': 'Test Orga',
        'path': 'testorga',
        'description': 'An interesting group',
        'visibility': 'public',
        'lfs_enabled': True,
        'avatar_url': 'https://secure.gravatar.com/avatar/test',
        'web_url': 'https://gitlab.com/groups/testorga',
        'request_access_enabled': False,
        'full_name': 'Test Orga',
        'full_path': 'testorga',
        'parent_id': None,
    }

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.project.repo = 'https://gitlab.com/testorga/testrepo'
        self.project.save()
        self.org = RemoteOrganization.objects.create(slug='testorga')
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.service = GitLabService(
            user=self.user,
            account=get(SocialAccount, user=self.user)
        )
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build, project=self.project, version=self.external_version, commit=1234,
        )
        self.integration = get(
            GitLabWebhook,
            project=self.project,
            provider_data={
                'id': '999999999'
            }
        )
        self.provider_data = [
            {
                'id': 1084320,
                'url': 'https://readthedocs.io/api/v2/webhook/test/99999999/',
            }
        ]

    def get_private_repo_data(self):
        """Manipulate repo response data to get private repo data."""
        data = self.repo_response_data.copy()
        data.update({
            'visibility': 'private',
        })
        return data

    def test_project_path_is_escaped(self):
        repo_id = self.service._get_repo_id(self.project)
        self.assertEqual(repo_id, 'testorga%2Ftestrepo')

        self.project.repo = 'https://gitlab.com/testorga/subgroup/testrepo.git'
        self.project.save()
        repo_id = self.service._get_repo_id(self.project)
        self.assertEqual(repo_id, 'testorga%2Fsubgroup%2Ftestrepo')

    def test_make_project_pass(self):
        repo = self.service.create_repository(
            self.repo_response_data, organization=self.org,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, 'testrepo')
        self.assertEqual(repo.full_name, 'testorga/testrepo')
        self.assertEqual(repo.remote_id, 42)
        self.assertEqual(repo.vcs_provider, GITLAB)
        self.assertEqual(repo.description, 'Test Repo')
        self.assertEqual(
            repo.avatar_url,
            'https://secure.gravatar.com/avatar/test',
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            'https://gitlab.com/testorga/testrepo.git',
        )
        self.assertEqual(repo.ssh_url, 'git@gitlab.com:testorga/testrepo.git')
        self.assertEqual(repo.html_url, 'https://gitlab.com/testorga/testrepo')
        self.assertTrue(repo.remote_repository_relations.first().admin)
        self.assertFalse(repo.private)

    def test_make_private_project_fail(self):
        repo = self.service.create_repository(
            self.get_private_repo_data(), organization=self.org,
            privacy=self.privacy,
        )
        self.assertIsNone(repo)

    def test_make_private_project_success(self):
        repo = self.service.create_repository(
            self.get_private_repo_data(), organization=self.org,
            privacy=constants.PRIVATE,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertTrue(repo.private, True)

    def test_make_organization(self):
        org = self.service.create_organization(self.group_response_data)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, 'testorga')
        self.assertEqual(org.name, 'Test Orga')
        self.assertEqual(
            org.avatar_url,
            'https://secure.gravatar.com/avatar/test',
        )
        self.assertEqual(org.url, 'https://gitlab.com/testorga')

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        data = self.repo_response_data.copy()
        data['visibility'] = 'public'
        repo = self.service.create_repository(data, organization=self.org)
        self.assertIsNotNone(repo)

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_send_build_status_successful(self, repo_id, session, mock_logger):
        session().post.return_value.status_code = 201
        repo_id().return_value = '9999'

        success = self.service.send_build_status(
            self.external_build,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS
        )

        self.assertTrue(success)
        mock_logger.bind.assert_called_with(http_status_code=201)
        mock_logger.info.assert_called_with(
            "GitLab commit status created for project.",
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_send_build_status_404_error(self, repo_id, session, mock_logger):
        session().post.return_value.status_code = 404
        repo_id.return_value = '9999'

        success = self.service.send_build_status(
            self.external_build,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.bind.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            'GitLab project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_send_build_status_value_error(self, repo_id, session, mock_logger):
        session().post.side_effect = ValueError
        repo_id().return_value = '9999'

        success = self.service.send_build_status(
            self.external_build, self.external_build.commit, BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            commit_status='success',
            user_username=self.user.username,
            url=mock.ANY,
        )
        mock_logger.exception.assert_called_with(
            'GitLab commit status creation failed.',
            debug_data=None,
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_setup_webhook_successful(self, session, mock_logger):
        session().post.return_value.status_code = 201
        session().post.return_value.json.return_value = {}
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            http_status_code=201,
        )
        mock_logger.info.assert_called_with(
            "GitLab webhook creation successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_setup_webhook_404_error(self, session, mock_logger):
        session().post.return_value.status_code = 404
        success, _ = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertFalse(success)
        self.assertIsNone(self.integration.secret)
        mock_logger.bind.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            'Gitlab project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_setup_webhook_value_error(self, session, mock_logger):
        session().post.side_effect = ValueError
        success = self.service.setup_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertIsNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url='https://gitlab.com/api/v4/projects/testorga%2Ftestrepo/hooks',
        )
        mock_logger.exception.assert_called_with(
            'GitLab webhook creation failed.',
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_update_webhook_successful(self, repo_id, session, mock_logger):
        repo_id.return_value = '9999'
        session().put.return_value.status_code = 200
        session().put.return_value.json.return_value = {}
        success, _ = self.service.update_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            "GitLab webhook update successful for project.",
        )

    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.setup_webhook')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_update_webhook_404_error(self, repo_id, setup_webhook, session):
        repo_id.return_value = '9999'
        session().put.return_value.status_code = 404
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.setup_webhook')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_update_webhook_no_provider_data(self, repo_id, setup_webhook, session):
        self.integration.provider_data = None
        self.integration.save()

        repo_id.return_value = '9999'
        session().put.side_effect = AttributeError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        setup_webhook.assert_called_once_with(
            self.project,
            self.integration
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService._get_repo_id')
    def test_update_webhook_value_error(self, repo_id, session, mock_logger):
        repo_id.return_value = '9999'
        session().put.side_effect = ValueError
        self.service.update_webhook(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertIsNone(self.integration.secret)
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.exception.assert_called_with(
            'GitLab webhook update failed.',
            debug_data=None,
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_get_provider_data_successful(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = 'https://{domain}{path}'.format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                'api_webhook',
                kwargs={
                    'project_slug': self.project.slug,
                    'integration_pk': self.integration.pk,
                },
            )
        )
        webhook_data[0]["url"] = rtd_webhook_url

        session().get.return_value.status_code = 200
        session().get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data[0])
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            'GitLab integration updated with provider data for project.',
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_get_provider_data_404_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.return_value.status_code = 404

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            'GitLab project does not exist or user does not have permissions.',
        )

    @mock.patch('readthedocs.oauth.services.gitlab.log')
    @mock.patch('readthedocs.oauth.services.gitlab.GitLabService.get_session')
    def test_get_provider_data_attribute_error(self, session, mock_logger):
        self.integration.provider_data = {}
        self.integration.save()

        session().get.side_effect = AttributeError

        self.service.get_provider_data(
            self.project,
            self.integration
        )

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.bind.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.exception.assert_called_with(
            'GitLab webhook Listing failed for project.',
        )
