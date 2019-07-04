# -*- coding: utf-8 -*-
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL, BUILD_STATUS_SUCCESS
from readthedocs.builds.models import Version, Build
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
        self.org = RemoteOrganization.objects.create(slug='rtfd', json='')
        self.privacy = self.project.version_privacy_level
        self.service = GitHubService(user=self.user, account=None)
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build, project=self.project, version=self.external_version
        )

    def test_make_project_pass(self):
        repo_json = {
            'name': 'testrepo',
            'full_name': 'testuser/testrepo',
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
        services = GitHubService.for_user(self.user)
        self.assertEqual(services, [])

    def test_multiple_users_same_repo(self):
        repo_json = {
            'name': '',
            'full_name': 'testrepo/multiple',
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
        service = GitHubService(user=user2, account=None)
        github_project_2 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy,
        )
        self.assertIsInstance(github_project, RemoteRepository)
        self.assertIsInstance(github_project_2, RemoteRepository)
        self.assertNotEqual(github_project_2, github_project)

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
            BUILD_STATUS_SUCCESS
        )

        self.assertTrue(success)
        mock_logger.info.assert_called_with(
            'GitHub commit status for project: %s',
            self.project
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_send_build_status_404_error(self, session, mock_logger):
        session().post.return_value.status_code = 404
        success = self.service.send_build_status(
            self.external_build,
            BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.info.assert_called_with(
            'GitHub project does not exist or user does not have '
            'permissions: project=%s',
            self.project
        )

    @mock.patch('readthedocs.oauth.services.github.log')
    @mock.patch('readthedocs.oauth.services.github.GitHubService.get_session')
    def test_send_build_status_value_error(self, session, mock_logger):
        session().post.side_effect = ValueError
        success = self.service.send_build_status(
            self.external_build, BUILD_STATUS_SUCCESS
        )

        self.assertFalse(success)
        mock_logger.exception.assert_called_with(
                'GitHub commit status creation failed for project: %s',
                self.project,
        )

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        repo_json = {
            'name': 'testrepo',
            'full_name': 'testuser/testrepo',
            'description': 'Test Repo',
            'git_url': 'git://github.com/testuser/testrepo.git',
            'private': False,
            'ssh_url': 'ssh://git@github.com:testuser/testrepo.git',
            'html_url': 'https://github.com/testuser/testrepo',
            'clone_url': 'https://github.com/testuser/testrepo.git',
        }
        repo = self.service.create_repository(repo_json, organization=self.org)
        self.assertIsNotNone(repo)


class BitbucketOAuthTests(TestCase):

    fixtures = ['eric', 'test_data']
    repo_response_data = {
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
    }

    team_response_data = {
        'username': 'teamsinspace',
        'website': None,
        'display_name': 'Teams In Space',
        'uuid': '{61fc5cf6-d054-47d2-b4a9-061ccf858379}',
        'links': {
            'self': {
                'href': 'https://api.bitbucket.org/2.0/teams/teamsinspace',
            },
            'repositories': {
                'href': 'https://api.bitbucket.org/2.0/repositories/teamsinspace',
            },
            'html': {'href': 'https://bitbucket.org/teamsinspace'},
            'followers': {
                'href': 'https://api.bitbucket.org/2.0/teams/teamsinspace/followers',
            },
            'avatar': {
                'href': 'https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/teamsinspace-avatar-3731530358-7_avatar.png',
            },
            'members': {
                'href': 'https://api.bitbucket.org/2.0/teams/teamsinspace/members',
            },
            'following': {
                'href': 'https://api.bitbucket.org/2.0/teams/teamsinspace/following',
            },
        },
        'created_on': '2014-04-08T00:00:14.070969+00:00',
        'location': None,
        'type': 'team',
    }

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.org = RemoteOrganization.objects.create(slug='rtfd', json='')
        self.privacy = self.project.version_privacy_level
        self.service = BitbucketService(user=self.user, account=None)

    def test_make_project_pass(self):
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
        services = BitbucketService.for_user(self.user)
        self.assertEqual(services, [])


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
        self.org = RemoteOrganization.objects.create(slug='testorga', json='')
        self.privacy = self.project.version_privacy_level
        self.service = GitLabService(user=self.user, account=None)

    def get_private_repo_data(self):
        """Manipulate repo response data to get private repo data."""
        data = self.repo_response_data.copy()
        data.update({
            'visibility': 'private',
        })
        return data

    def test_make_project_pass(self):
        with mock.patch('readthedocs.oauth.services.gitlab.GitLabService.is_owned_by') as m:  # yapf: disable
            m.return_value = True
            repo = self.service.create_repository(
                self.repo_response_data, organization=self.org,
                privacy=self.privacy,
            )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, 'testrepo')
        self.assertEqual(repo.full_name, 'testorga / testrepo')
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
        self.assertTrue(repo.admin)
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
        with mock.patch('readthedocs.oauth.services.gitlab.GitLabService.is_owned_by') as m:  # yapf: disable
            m.return_value = True
            repo = self.service.create_repository(data, organization=self.org)
        self.assertIsNotNone(repo)

    def test_setup_webhook(self):
        success, response = self.service.setup_webhook(self.project)
        self.assertFalse(success)
        self.assertIsNone(response)
