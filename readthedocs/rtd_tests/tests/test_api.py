# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import base64
import datetime
import json
from builtins import str

import mock
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.test import APIClient

from readthedocs.builds.models import Build, Version
from readthedocs.integrations.models import Integration
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Feature, Project

super_auth = base64.b64encode(b'super:test').decode('utf-8')
eric_auth = base64.b64encode(b'eric:test').decode('utf-8')


class APIBuildTests(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def test_make_build(self):
        """Test that a superuser can use the API."""
        client = APIClient()
        client.login(username='super', password='test')
        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'success': True,
                'output': 'Test Output',
                'error': 'Test Error',
                'state': 'cloning',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build = resp.data
        self.assertEqual(build['state_display'], 'Cloning')

        resp = client.get('/api/v2/build/%s/' % build['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(build['output'], 'Test Output')
        self.assertEqual(build['state_display'], 'Cloning')

    def test_make_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot write the build endpoint."""
        client = APIClient()

        def _try_post():
            resp = client.post(
                '/api/v2/build/',
                {
                    'project': 1,
                    'version': 1,
                    'success': True,
                    'output': 'Test Output',
                    'error': 'Test Error',
                },
                format='json',
            )
            self.assertEqual(resp.status_code, 403)

        _try_post()

        api_user = get(User, staff=False, password='test')
        assert api_user.is_staff is False
        client.force_authenticate(user=api_user)
        _try_post()

    def test_update_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot update build endpoints."""
        client = APIClient()
        api_user = get(User, staff=False, password='test')
        client.force_authenticate(user=api_user)
        build = get(Build, project_id=1, version_id=1, state='cloning')
        resp = client.put(
            '/api/v2/build/{0}/'.format(build.pk),
            {
                'project': 1,
                'version': 1,
                'state': 'finished',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_make_build_protected_fields(self):
        """
        Ensure build api view delegates correct serializer.

        Super users should be able to read/write the `builder` property, but we
        don't expose this to end users via the API
        """
        build = get(Build, project_id=1, version_id=1, builder='foo')
        client = APIClient()

        api_user = get(User, staff=False, password='test')
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{0}/'.format(build.pk), format='json')
        self.assertEqual(resp.status_code, 200)

        client.force_authenticate(user=User.objects.get(username='super'))
        resp = client.get('/api/v2/build/{0}/'.format(build.pk), format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('builder', resp.data)

    def test_make_build_commands(self):
        """Create build and build commands."""
        client = APIClient()
        client.login(username='super', password='test')
        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'success': True,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build = resp.data
        now = datetime.datetime.utcnow()
        resp = client.post(
            '/api/v2/command/',
            {
                'build': build['id'],
                'command': 'echo test',
                'description': 'foo',
                'exit_code': 0,
                'start_time': str(now - datetime.timedelta(seconds=5)),
                'end_time': str(now),
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = client.get('/api/v2/build/%s/' % build['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(len(build['commands']), 1)
        self.assertEqual(build['commands'][0]['run_time'], 5)
        self.assertEqual(build['commands'][0]['description'], 'foo')


class APITests(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def test_make_project(self):
        """Test that a superuser can use the API."""
        post_data = {
            'name': 'awesome-project',
            'repo': 'https://github.com/ericholscher/django-kong.git',
        }
        resp = self.client.post(
            '/api/v1/project/',
            data=json.dumps(post_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic %s' % super_auth,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'], '/api/v1/project/24/')
        resp = self.client.get(
            '/api/v1/project/24/',
            data={'format': 'json'},
            HTTP_AUTHORIZATION='Basic %s' % eric_auth,
        )
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['slug'], 'awesome-project')

    def test_user_doesnt_get_full_api_return(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)
        project = get(Project, main_language_project=None, conf_py_file='foo')
        client = APIClient()

        client.force_authenticate(user=user_normal)
        resp = client.get('/api/v2/project/%s/' % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('conf_py_file', resp.data)

        client.force_authenticate(user=user_admin)
        resp = client.get('/api/v2/project/%s/' % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('conf_py_file', resp.data)
        self.assertEqual(resp.data['conf_py_file'], 'foo')

    def test_invalid_make_project(self):
        """Test that the authentication is turned on."""
        post_data = {
            'user': '/api/v1/user/2/',
            'name': 'awesome-project-2',
            'repo': 'https://github.com/ericholscher/django-bob.git',
        }
        resp = self.client.post(
            '/api/v1/project/',
            data=json.dumps(post_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic %s' %
            base64.b64encode(b'tester:notapass').decode('utf-8'),
        )
        self.assertEqual(resp.status_code, 401)

    def test_make_project_dishonest_user(self):
        """Test that you can't create a project for another user."""
        # represents dishonest data input, authentication happens for user 2
        post_data = {
            'users': ['/api/v1/user/1/'],
            'name': 'awesome-project-2',
            'repo': 'https://github.com/ericholscher/django-bob.git',
        }
        resp = self.client.post(
            '/api/v1/project/',
            data=json.dumps(post_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic %s' %
            base64.b64encode(b'tester:test').decode('utf-8'),
        )
        self.assertEqual(resp.status_code, 401)

    def test_ensure_get_unauth(self):
        """Test that GET requests work without authenticating."""
        resp = self.client.get('/api/v1/project/', data={'format': 'json'})
        self.assertEqual(resp.status_code, 200)

    def test_project_features(self):
        user = get(User, is_staff=True)
        project = get(Project, main_language_project=None)
        # One explicit, one implicit feature
        feature1 = get(Feature, projects=[project])
        feature2 = get(Feature, projects=[], default_true=True)
        feature3 = get(Feature, projects=[], default_true=False)  # noqa
        client = APIClient()

        client.force_authenticate(user=user)
        resp = client.get('/api/v2/project/%s/' % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('features', resp.data)
        self.assertEqual(
            resp.data['features'],
            [feature1.feature_id, feature2.feature_id],
        )

    def test_project_features_multiple_projects(self):
        user = get(User, is_staff=True)
        project1 = get(Project, main_language_project=None)
        project2 = get(Project, main_language_project=None)
        feature = get(Feature, projects=[project1, project2], default_true=True)
        client = APIClient()

        client.force_authenticate(user=user)
        resp = client.get('/api/v2/project/%s/' % (project1.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('features', resp.data)
        self.assertEqual(resp.data['features'], [feature.feature_id])

    def test_project_pagination(self):
        for _ in range(100):
            get(Project)

        resp = self.client.get('/api/v2/project/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 100)  # page_size
        self.assertIn('?page=2', resp.data['next'])

    def test_remote_repository_pagination(self):
        account = get(SocialAccount, provider='github')
        user = get(User, socialaccount_set=[account])
        for _ in range(20):
            get(RemoteRepository, users=[user], account=account)

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get('/api/v2/remote/repo/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 15)  # page_size
        self.assertIn('?page=2', resp.data['next'])

    def test_remote_organization_pagination(self):
        account = get(SocialAccount, provider='github')
        user = get(User, socialaccount_set=[account])
        for _ in range(30):
            get(RemoteOrganization, users=[user], account=account)

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get('/api/v2/remote/org/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 25)  # page_size
        self.assertIn('?page=2', resp.data['next'])


class APIImportTests(TestCase):

    """Import API endpoint tests."""

    fixtures = ['eric.json', 'test_data.json']

    def test_permissions(self):
        """Ensure user repositories aren't leaked to other users."""
        client = APIClient()

        account_a = get(SocialAccount, provider='github')
        account_b = get(SocialAccount, provider='github')
        account_c = get(SocialAccount, provider='github')
        user_a = get(User, password='test', socialaccount_set=[account_a])
        user_b = get(User, password='test', socialaccount_set=[account_b])
        user_c = get(User, password='test', socialaccount_set=[account_c])
        org_a = get(RemoteOrganization, users=[user_a], account=account_a)
        repo_a = get(
            RemoteRepository,
            users=[user_a],
            organization=org_a,
            account=account_a,
        )
        repo_b = get(
            RemoteRepository,
            users=[user_b],
            organization=None,
            account=account_b,
        )

        client.force_authenticate(user=user_a)
        resp = client.get('/api/v2/remote/repo/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(repos[0]['id'], repo_a.id)
        self.assertEqual(repos[0]['organization']['id'], org_a.id)
        self.assertEqual(len(repos), 1)

        resp = client.get('/api/v2/remote/org/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        orgs = resp.data['results']
        self.assertEqual(orgs[0]['id'], org_a.id)
        self.assertEqual(len(orgs), 1)

        client.force_authenticate(user=user_b)
        resp = client.get('/api/v2/remote/repo/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(repos[0]['id'], repo_b.id)
        self.assertEqual(repos[0]['organization'], None)
        self.assertEqual(len(repos), 1)

        client.force_authenticate(user=user_c)
        resp = client.get('/api/v2/remote/repo/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(len(repos), 0)


@mock.patch('readthedocs.core.views.hooks.trigger_build')
class IntegrationsTests(TestCase):

    """Integration for webhooks, etc."""

    fixtures = ['eric.json', 'test_data.json']

    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, verbose_name='master', project=self.project)

    def test_github_webhook(self, trigger_build):
        """GitHub webhook API."""
        client = APIClient()
        client.post(
            '/api/v2/webhook/github/{0}/'.format(self.project.slug),
            {'ref': 'master'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])
        client.post(
            '/api/v2/webhook/github/{0}/'.format(self.project.slug),
            {'ref': 'non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])

    def test_github_invalid_webhook(self, trigger_build):
        """GitHub webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(self.project.slug),
            {'foo': 'bar'},
            format='json',
            HTTP_X_GITHUB_EVENT='pull_request',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_gitlab_webhook(self, trigger_build):
        """GitLab webhook API."""
        client = APIClient()
        client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'push', 'ref': 'master'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])
        client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'push', 'ref': 'non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])

    def test_gitlab_invalid_webhook(self, trigger_build):
        """GitLab webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'pull_request'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_bitbucket_webhook(self, trigger_build):
        """Bitbucket webhook API."""
        client = APIClient()
        client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [{
                        'new': {
                            'name': 'master',
                        },
                    }],
                },
            },
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])
        client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [
                        {
                            'new': {'name': 'non-existent'},
                        },
                    ],
                },
            },
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)])

        client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [
                        {
                            'new': None,
                        },
                    ],
                },
            },
            format='json',
        )
        trigger_build.assert_not_called(
            [mock.call(force=True, version=mock.ANY, project=self.project)])

    def test_bitbucket_invalid_webhook(self, trigger_build):
        """Bitbucket webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {'foo': 'bar'}, format='json', HTTP_X_EVENT_KEY='pull_request')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_generic_api_fails_without_auth(self, trigger_build):
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/generic/{0}/'.format(self.project.slug),
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.data['detail'],
            'Authentication credentials were not provided.',
        )

    def test_generic_api_respects_token_auth(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )
        self.assertIsNotNone(integration.token)
        resp = client.post(
            '/api/v2/webhook/{0}/{1}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])
        # Test nonexistent branch
        resp = client.post(
            '/api/v2/webhook/{0}/{1}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token, 'branches': 'nonexistent'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['build_triggered'])

    def test_generic_api_respects_basic_auth(self, trigger_build):
        client = APIClient()
        user = get(User)
        self.project.users.add(user)
        client.force_authenticate(user=user)
        resp = client.post(
            '/api/v2/webhook/generic/{0}/'.format(self.project.slug),
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])

    def test_generic_api_falls_back_to_token_auth(self, trigger_build):
        client = APIClient()
        user = get(User)
        client.force_authenticate(user=user)
        integration = Integration.objects.create(
            project=self.project, integration_type=Integration.API_WEBHOOK)
        self.assertIsNotNone(integration.token)
        resp = client.post(
            '/api/v2/webhook/{0}/{1}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])


class APIVersionTests(TestCase):
    fixtures = ['eric', 'test_data']

    def test_get_version_by_id(self):
        """
        Test the full response of ``/api/v2/version/{pk}`` is what we expects.

        Allows us to notice changes in the fields returned by the endpoint
        instead of let them pass silently.
        """
        pip = Project.objects.get(slug='pip')
        version = pip.versions.get(slug='0.8')

        data = {
            'pk': version.pk,
        }
        resp = self.client.get(
            reverse('version-detail', kwargs=data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic {}'.format(eric_auth),
        )
        self.assertEqual(resp.status_code, 200)

        version_data = {
            'type': 'tag',
            'verbose_name': '0.8',
            'built': False,
            'id': 18,
            'active': True,
            'project': {
                'analytics_code': None,
                'canonical_url': 'http://readthedocs.org/docs/pip/en/latest/',
                'cdn_enabled': False,
                'conf_py_file': '',
                'container_image': None,
                'container_mem_limit': None,
                'container_time_limit': None,
                'default_branch': None,
                'default_version': 'latest',
                'description': '',
                'documentation_type': 'sphinx',
                'enable_epub_build': True,
                'enable_pdf_build': True,
                'features': ['allow_deprecated_webhooks'],
                'id': 6,
                'install_project': False,
                'language': 'en',
                'name': 'Pip',
                'programming_language': 'words',
                'python_interpreter': 'python',
                'repo': 'https://github.com/pypa/pip',
                'repo_type': 'git',
                'requirements_file': None,
                'skip': False,
                'slug': 'pip',
                'suffix': '.rst',
                'use_system_packages': False,
                'users': [1],
            },
            'downloads': {},
            'identifier': '2404a34eba4ee9c48cc8bc4055b99a48354f4950',
            'slug': '0.8',
        }

        self.assertDictEqual(
            resp.data,
            version_data,
        )
