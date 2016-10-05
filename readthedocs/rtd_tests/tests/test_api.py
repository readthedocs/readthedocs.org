import json
import base64
import datetime

import mock
from django.test import TestCase
from django.contrib.auth.models import User
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.test import APIClient
from allauth.socialaccount.models import SocialAccount

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.oauth.models import RemoteRepository, RemoteOrganization


super_auth = base64.b64encode('super:test')
eric_auth = base64.b64encode('eric:test')


class APIBuildTests(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def test_make_build(self):
        """
        Test that a superuser can use the API
        """
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
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build = resp.data
        self.assertEqual(build['state_display'], 'Cloning')

        resp = client.get('/api/v2/build/%s/' % build['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(build['output'], 'Test Output')
        self.assertEqual(build['state_display'], 'Cloning')

    def test_make_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot write the build endpoint"""
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
                format='json')
            self.assertEqual(resp.status_code, 403)

        _try_post()

        api_user = get(User, staff=False, password='test')
        assert api_user.is_staff is False
        client.force_authenticate(user=api_user)
        _try_post()

    def test_update_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot update build endpoints"""
        client = APIClient()
        api_user = get(User, staff=False, password='test')
        client.force_authenticate(user=api_user)
        build = get(Build, project_id=1, version_id=1, state='cloning')
        resp = client.put(
            '/api/v2/build/{0}/'.format(build.pk),
            {
                'project': 1,
                'version': 1,
                'state': 'finished'
            },
            format='json')
        self.assertEqual(resp.status_code, 403)

    def test_make_build_protected_fields(self):
        """Ensure build api view delegates correct serializer

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
        """Create build and build commands"""
        client = APIClient()
        client.login(username='super', password='test')
        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'success': True,
            },
            format='json')
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
            format='json')
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
        """
        Test that a superuser can use the API
        """
        post_data = {"name": "awesome-project",
                     "repo": "https://github.com/ericholscher/django-kong.git"}
        resp = self.client.post('/api/v1/project/',
                                data=json.dumps(post_data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION='Basic %s' % super_auth)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'],
                         'http://testserver/api/v1/project/24/')
        resp = self.client.get('/api/v1/project/24/', data={'format': 'json'},
                               HTTP_AUTHORIZATION='Basic %s' % eric_auth)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['slug'], 'awesome-project')

    def test_invalid_make_project(self):
        """
        Test that the authentication is turned on.
        """
        post_data = {"user": "/api/v1/user/2/",
                     "name": "awesome-project-2",
                     "repo": "https://github.com/ericholscher/django-bob.git"
                     }
        resp = self.client.post(
            '/api/v1/project/', data=json.dumps(post_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic %s' % base64.b64encode('tester:notapass')
        )
        self.assertEqual(resp.status_code, 401)

    def test_make_project_dishonest_user(self):
        """
        Test that you can't create a project for another user
        """
        # represents dishonest data input, authentication happens for user 2
        post_data = {
            "users": ["/api/v1/user/1/"],
            "name": "awesome-project-2",
            "repo": "https://github.com/ericholscher/django-bob.git"
        }
        resp = self.client.post(
            '/api/v1/project/',
            data=json.dumps(post_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic %s' % base64.b64encode('tester:test')
        )
        self.assertEqual(resp.status_code, 401)

    def test_ensure_get_unauth(self):
        """
        Test that GET requests work without authenticating.
        """

        resp = self.client.get("/api/v1/project/", data={"format": "json"})
        self.assertEqual(resp.status_code, 200)

    def test_not_highest(self):
        resp = self.client.get(
            "http://testserver/api/v1/version/read-the-docs/highest/0.2.1/",
            data={"format": "json"}
        )
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['is_highest'], False)

    def test_latest_version_highest(self):
        resp = self.client.get(
            "http://testserver/api/v1/version/read-the-docs/highest/latest/",
            data={"format": "json"}
        )
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['is_highest'], True)

    def test_real_highest(self):
        resp = self.client.get(
            "http://testserver/api/v1/version/read-the-docs/highest/0.2.2/",
            data={"format": "json"}
        )
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['is_highest'], True)


class APIImportTests(TestCase):

    """Import API endpoint tests"""

    fixtures = ['eric.json', 'test_data.json']

    def test_permissions(self):
        """Ensure user repositories aren't leaked to other users"""
        client = APIClient()

        account_a = get(SocialAccount, provider='github')
        account_b = get(SocialAccount, provider='github')
        account_c = get(SocialAccount, provider='github')
        user_a = get(User, password='test', socialaccount_set=[account_a])
        user_b = get(User, password='test', socialaccount_set=[account_b])
        user_c = get(User, password='test', socialaccount_set=[account_c])
        org_a = get(RemoteOrganization, users=[user_a], account=account_a)
        repo_a = get(RemoteRepository, users=[user_a], organization=org_a,
                     account=account_a)
        repo_b = get(RemoteRepository, users=[user_b], organization=None,
                     account=account_b)

        client.force_authenticate(user=user_a)
        resp = client.get(
            '/api/v2/remote/repo/',
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(repos[0]['id'], repo_a.id)
        self.assertEqual(repos[0]['organization']['id'], org_a.id)
        self.assertEqual(len(repos), 1)

        resp = client.get(
            '/api/v2/remote/org/',
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        orgs = resp.data['results']
        self.assertEqual(orgs[0]['id'], org_a.id)
        self.assertEqual(len(orgs), 1)

        client.force_authenticate(user=user_b)
        resp = client.get(
            '/api/v2/remote/repo/',
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(repos[0]['id'], repo_b.id)
        self.assertEqual(repos[0]['organization'], None)
        self.assertEqual(len(repos), 1)

        client.force_authenticate(user=user_c)
        resp = client.get(
            '/api/v2/remote/repo/',
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data['results']
        self.assertEqual(len(repos), 0)


@mock.patch('readthedocs.core.views.hooks.trigger_build')
class IntegrationsTests(TestCase):

    """Integration for webhooks, etc"""

    fixtures = ['eric.json', 'test_data.json']

    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, verbose_name='master', project=self.project)

    def test_github_webhook(self, trigger_build):
        """GitHub webhook API"""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(self.project.slug),
            {'ref': 'master'},
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(self.project.slug),
            {'ref': 'non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])

    def test_github_invalid_webhook(self, trigger_build):
        """GitHub webhook unhandled event"""
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
        """GitLab webhook API"""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'push', 'ref': 'master'},
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])
        resp = client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'push', 'ref': 'non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])

    def test_gitlab_invalid_webhook(self, trigger_build):
        """GitLab webhook unhandled event"""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/gitlab/{0}/'.format(self.project.slug),
            {'object_kind': 'pull_request'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_bitbucket_webhook(self, trigger_build):
        """Bitbucket webhook API"""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [{
                        'new': {
                            'name': 'master'
                        }
                    }]
                }
            },
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])
        resp = client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [{
                        'new': {
                            'name': 'non-existent'
                        }
                    }]
                }
            },
            format='json',
        )
        trigger_build.assert_has_calls([
            mock.call(force=True, version=mock.ANY, project=self.project)
        ])

    def test_bitbucket_invalid_webhook(self, trigger_build):
        """Bitbucket webhook unhandled event"""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/bitbucket/{0}/'.format(self.project.slug),
            {'foo': 'bar'},
            format='json',
            HTTP_X_EVENT_KEY='pull_request'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')
