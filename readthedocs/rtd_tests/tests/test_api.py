import base64
import datetime
import json

from unittest import mock
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.test import APIClient

from readthedocs.api.v2.views.integrations import (
    GITHUB_CREATE,
    GITHUB_DELETE,
    GITHUB_EVENT_HEADER,
    GITHUB_PUSH,
    GITHUB_SIGNATURE_HEADER,
    GITHUB_PULL_REQUEST,
    GITHUB_PULL_REQUEST_OPENED,
    GITHUB_PULL_REQUEST_REOPENED,
    GITHUB_PULL_REQUEST_CLOSED,
    GITHUB_PULL_REQUEST_SYNC,
    GITLAB_MERGE_REQUEST,
    GITLAB_MERGE_REQUEST_CLOSE,
    GITLAB_MERGE_REQUEST_MERGE,
    GITLAB_MERGE_REQUEST_OPEN,
    GITLAB_MERGE_REQUEST_REOPEN,
    GITLAB_MERGE_REQUEST_UPDATE,
    GITLAB_NULL_HASH,
    GITLAB_PUSH,
    GITLAB_TAG_PUSH,
    GITLAB_TOKEN_HEADER,
    GitHubWebhookView,
    GitLabWebhookView,
)
from readthedocs.api.v2.views.task_views import get_status_data
from readthedocs.builds.constants import LATEST, EXTERNAL
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.integrations.models import Integration
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import (
    APIProject,
    EnvironmentVariable,
    Feature,
    Project,
)


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
        self.assertEqual(build['config'], {})

        resp = client.get('/api/v2/build/%s/' % build['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(build['output'], 'Test Output')
        self.assertEqual(build['state_display'], 'Cloning')

    def test_api_does_not_have_private_config_key_superuser(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = Build.objects.create(project=project, version=version)

        resp = client.get('/api/v2/build/{}/'.format(build.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('config', resp.data)
        self.assertNotIn('_config', resp.data)

    def test_api_does_not_have_private_config_key_normal_user(self):
        client = APIClient()
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = Build.objects.create(project=project, version=version)

        resp = client.get('/api/v2/build/{}/'.format(build.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('config', resp.data)
        self.assertNotIn('_config', resp.data)

    def test_save_config(self):
        client = APIClient()
        client.login(username='super', password='test')
        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'config': {'one': 'two'},
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build_one = resp.data
        self.assertEqual(build_one['config'], {'one': 'two'})

        resp = client.get('/api/v2/build/%s/' % build_one['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(build['config'], {'one': 'two'})

    def test_save_same_config(self):
        client = APIClient()
        client.login(username='super', password='test')
        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'config': {'one': 'two'},
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build_one = resp.data
        self.assertEqual(build_one['config'], {'one': 'two'})

        resp = client.post(
            '/api/v2/build/',
            {
                'project': 1,
                'version': 1,
                'config': {'one': 'two'},
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        build_two = resp.data
        self.assertEqual(build_two['config'], {'one': 'two'})

        resp = client.get('/api/v2/build/%s/' % build_one['id'])
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(build['config'], {'one': 'two'})

        # Checking the values from the db, just to be sure the
        # api isn't lying.
        self.assertEqual(
            Build.objects.get(pk=build_one['id'])._config,
            {'one': 'two'},
        )
        self.assertEqual(
            Build.objects.get(pk=build_two['id'])._config,
            {Build.CONFIG_KEY: build_one['id']},
        )

    def test_save_same_config_using_patch(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build_one = Build.objects.create(project=project, version=version)
        resp = client.patch(
            '/api/v2/build/{}/'.format(build_one.pk),
            {'config': {'one': 'two'}},
            format='json',
        )
        self.assertEqual(resp.data['config'], {'one': 'two'})

        build_two = Build.objects.create(project=project, version=version)
        resp = client.patch(
            '/api/v2/build/{}/'.format(build_two.pk),
            {'config': {'one': 'two'}},
            format='json',
        )
        self.assertEqual(resp.data['config'], {'one': 'two'})

        resp = client.get('/api/v2/build/{}/'.format(build_one.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        build = resp.data
        self.assertEqual(build['config'], {'one': 'two'})

        # Checking the values from the db, just to be sure the
        # api isn't lying.
        self.assertEqual(
            Build.objects.get(pk=build_one.pk)._config,
            {'one': 'two'},
        )
        self.assertEqual(
            Build.objects.get(pk=build_two.pk)._config,
            {Build.CONFIG_KEY: build_one.pk},
        )

    def test_response_building(self):
        """The ``view docs`` attr should return a link to the dashboard."""
        client = APIClient()
        client.login(username='super', password='test')
        project = get(
            Project,
            language='en',
            main_language_project=None,
        )
        version = get(
            Version,
            project=project,
            built=False,
            uploaded=False,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state='cloning',
            exit_code=0,
        )
        resp = client.get('/api/v2/build/{build}/'.format(build=build.pk))
        self.assertEqual(resp.status_code, 200)

        dashboard_url = reverse(
            'project_version_detail',
            kwargs={
                'project_slug': project.slug,
                'version_slug': version.slug,
            },
        )
        build = resp.data
        self.assertEqual(build['state'], 'cloning')
        self.assertEqual(build['error'], '')
        self.assertEqual(build['exit_code'], 0)
        self.assertEqual(build['success'], True)
        self.assertEqual(build['docs_url'], dashboard_url)

    def test_response_finished_and_success(self):
        """The ``view docs`` attr should return a link to the docs."""
        client = APIClient()
        client.login(username='super', password='test')
        project = get(
            Project,
            language='en',
            main_language_project=None,
        )
        version = get(
            Version,
            project=project,
            built=True,
            uploaded=True,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state='finished',
            exit_code=0,
        )
        resp = client.get('/api/v2/build/{build}/'.format(build=build.pk))
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        docs_url = 'http://readthedocs.org/docs/{project}/en/{version}/'.format(
            project=project.slug,
            version=version.slug,
        )
        self.assertEqual(build['state'], 'finished')
        self.assertEqual(build['error'], '')
        self.assertEqual(build['exit_code'], 0)
        self.assertEqual(build['success'], True)
        self.assertEqual(build['docs_url'], docs_url)

    def test_response_finished_and_fail(self):
        """The ``view docs`` attr should return a link to the dashboard."""
        client = APIClient()
        client.login(username='super', password='test')
        project = get(
            Project,
            language='en',
            main_language_project=None,
        )
        version = get(
            Version,
            project=project,
            built=False,
            uploaded=False,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state='finished',
            success=False,
            exit_code=1,
        )

        resp = client.get('/api/v2/build/{build}/'.format(build=build.pk))
        self.assertEqual(resp.status_code, 200)

        dashboard_url = reverse(
            'project_version_detail',
            kwargs={
                'project_slug': project.slug,
                'version_slug': version.slug,
            },
        )
        build = resp.data
        self.assertEqual(build['state'], 'finished')
        self.assertEqual(build['error'], '')
        self.assertEqual(build['exit_code'], 1)
        self.assertEqual(build['success'], False)
        self.assertEqual(build['docs_url'], dashboard_url)

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

        api_user = get(User, is_staff=False, password='test')
        assert api_user.is_staff is False
        client.force_authenticate(user=api_user)
        _try_post()

    def test_update_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot update build endpoints."""
        client = APIClient()
        api_user = get(User, is_staff=False, password='test')
        client.force_authenticate(user=api_user)
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(Build, project=project, version=version, state='cloning')
        resp = client.put(
            '/api/v2/build/{}/'.format(build.pk),
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
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(Build, project=project, version=version, builder='foo')
        client = APIClient()

        api_user = get(User, is_staff=False, password='test')
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{}/'.format(build.pk), format='json')
        self.assertEqual(resp.status_code, 200)

        client.force_authenticate(user=User.objects.get(username='super'))
        resp = client.get('/api/v2/build/{}/'.format(build.pk), format='json')
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

    def test_get_raw_log_success(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(Build, project=project, version=version, builder='foo')
        get(
            BuildCommandResult,
            build=build,
            command='python setup.py install',
            output='Installing dependencies...',
        )
        get(
            BuildCommandResult,
            build=build,
            command='git checkout master',
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{}.txt'.format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn('Read the Docs build information', resp.content.decode())
        self.assertIn('Build id: {}'.format(build.id), resp.content.decode())
        self.assertIn('Project: {}'.format(build.project.slug), resp.content.decode())
        self.assertIn('Version: {}'.format(build.version.slug), resp.content.decode())
        self.assertIn('Commit: {}'.format(build.commit), resp.content.decode())
        self.assertIn('Date: ', resp.content.decode())
        self.assertIn('State: finished', resp.content.decode())
        self.assertIn('Success: True', resp.content.decode())
        self.assertIn('[rtd-command-info]', resp.content.decode())
        self.assertIn(
            'python setup.py install\nInstalling dependencies...',
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_raw_log_building(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(
            Build, project=project, version=version,
            builder='foo', success=False,
            exit_code=1, state='building',
        )
        get(
            BuildCommandResult,
            build=build,
            command='python setup.py install',
            output='Installing dependencies...',
            exit_code=1,
        )
        get(
            BuildCommandResult,
            build=build,
            command='git checkout master',
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{}.txt'.format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn('Read the Docs build information', resp.content.decode())
        self.assertIn('Build id: {}'.format(build.id), resp.content.decode())
        self.assertIn('Project: {}'.format(build.project.slug), resp.content.decode())
        self.assertIn('Version: {}'.format(build.version.slug), resp.content.decode())
        self.assertIn('Commit: {}'.format(build.commit), resp.content.decode())
        self.assertIn('Date: ', resp.content.decode())
        self.assertIn('State: building', resp.content.decode())
        self.assertIn('Success: Unknow', resp.content.decode())
        self.assertIn('[rtd-command-info]', resp.content.decode())
        self.assertIn(
            'python setup.py install\nInstalling dependencies...',
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_raw_log_failure(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(
            Build, project=project, version=version,
            builder='foo', success=False, exit_code=1,
        )
        get(
            BuildCommandResult,
            build=build,
            command='python setup.py install',
            output='Installing dependencies...',
            exit_code=1,
        )
        get(
            BuildCommandResult,
            build=build,
            command='git checkout master',
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{}.txt'.format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn('Read the Docs build information', resp.content.decode())
        self.assertIn('Build id: {}'.format(build.id), resp.content.decode())
        self.assertIn('Project: {}'.format(build.project.slug), resp.content.decode())
        self.assertIn('Version: {}'.format(build.version.slug), resp.content.decode())
        self.assertIn('Commit: {}'.format(build.commit), resp.content.decode())
        self.assertIn('Date: ', resp.content.decode())
        self.assertIn('State: finished', resp.content.decode())
        self.assertIn('Success: False', resp.content.decode())
        self.assertIn('[rtd-command-info]', resp.content.decode())
        self.assertIn(
            'python setup.py install\nInstalling dependencies...',
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_invalid_raw_log(self):
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/{}.txt'.format(404))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_build_filter_by_commit(self):
        """
        Create a build with commit
        Should return the list of builds according to the
        commit query params
        """
        project1 = Project.objects.get(pk=1)
        project2 = Project.objects.get(pk=2)
        version1 = project1.versions.first()
        version2 = project2.versions.first()
        get(Build, project=project1, version=version1, builder='foo', commit='test')
        get(Build, project=project2, version=version2, builder='foo', commit='other')
        client = APIClient()
        api_user = get(User, is_staff=False, password='test')
        client.force_authenticate(user=api_user)
        resp = client.get('/api/v2/build/', {'commit': 'test'}, format='json')
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(len(build['results']), 1)


class APITests(TestCase):
    fixtures = ['eric.json', 'test_data.json']

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

    def test_project_features(self):
        user = get(User, is_staff=True)
        project = get(Project, main_language_project=None)
        # One explicit, one implicit feature
        feature1 = get(Feature, projects=[project])
        feature2 = get(Feature, projects=[], past_default_true=True)
        feature3 = get(Feature, projects=[], past_default_true=False)  # noqa
        client = APIClient()

        client.force_authenticate(user=user)
        resp = client.get('/api/v2/project/%s/' % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('features', resp.data)
        self.assertCountEqual(
            resp.data['features'],
            [feature1.feature_id, feature2.feature_id],
        )

    def test_project_features_multiple_projects(self):
        user = get(User, is_staff=True)
        project1 = get(Project, main_language_project=None)
        project2 = get(Project, main_language_project=None)
        feature = get(Feature, projects=[project1, project2], past_default_true=True)
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
        user = get(User)
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
        user = get(User)
        for _ in range(30):
            get(RemoteOrganization, users=[user], account=account)

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get('/api/v2/remote/org/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 25)  # page_size
        self.assertIn('?page=2', resp.data['next'])

    def test_project_environment_variables(self):
        user = get(User, is_staff=True)
        project = get(Project, main_language_project=None)
        get(
            EnvironmentVariable,
            name='TOKEN',
            value='a1b2c3',
            project=project,
        )

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get('/api/v2/project/%s/' % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('environment_variables', resp.data)
        self.assertEqual(
            resp.data['environment_variables'],
            {'TOKEN': 'a1b2c3'},
        )

    def test_init_api_project(self):
        project_data = {
            'name': 'Test Project',
            'slug': 'test-project',
            'show_advertising': True,
        }

        api_project = APIProject(**project_data)
        self.assertEqual(api_project.slug, 'test-project')
        self.assertEqual(api_project.features, [])
        self.assertFalse(api_project.ad_free)
        self.assertTrue(api_project.show_advertising)
        self.assertEqual(api_project.environment_variables, {})

        project_data['features'] = ['test-feature']
        project_data['show_advertising'] = False
        project_data['environment_variables'] = {'TOKEN': 'a1b2c3'}
        api_project = APIProject(**project_data)
        self.assertEqual(api_project.features, ['test-feature'])
        self.assertTrue(api_project.ad_free)
        self.assertFalse(api_project.show_advertising)
        self.assertEqual(api_project.environment_variables, {'TOKEN': 'a1b2c3'})

    def test_concurrent_builds(self):
        expected = {
            'limit_reached': False,
            'concurrent': 2,
            'max_concurrent': 4,
        }
        user = get(User, is_staff=True)
        project = get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        for state in ('triggered', 'building', 'cloning', 'finished'):
            get(
                Build,
                project=project,
                state=state,
            )

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get(f'/api/v2/build/concurrent/', data={'project__slug': project.slug})
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(expected, resp.data)


class APIImportTests(TestCase):

    """Import API endpoint tests."""

    fixtures = ['eric.json', 'test_data.json']

    def test_permissions(self):
        """Ensure user repositories aren't leaked to other users."""
        client = APIClient()

        account_a = get(SocialAccount, provider='github')
        account_b = get(SocialAccount, provider='github')
        account_c = get(SocialAccount, provider='github')
        user_a = get(User, password='test')
        user_b = get(User, password='test')
        user_c = get(User, password='test')
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
        self.project = get(
            Project,
            build_queue=None,
            external_builds_enabled=True,
        )
        self.feature_flag = get(
            Feature,
            projects=[self.project],
            feature_id=Feature.EXTERNAL_VERSION_BUILD,
        )
        self.version = get(
            Version, slug='master', verbose_name='master',
            active=True, project=self.project,
        )
        self.version_tag = get(
            Version, slug='v1.0', verbose_name='v1.0',
            active=True, project=self.project,
        )
        self.github_payload = {
            'ref': 'master',
        }
        self.commit = "ec26de721c3235aad62de7213c562f8c821"
        self.github_pull_request_payload = {
            "action": "opened",
            "number": 2,
            "pull_request": {
                "head": {
                    "sha": self.commit
                }
            }
        }
        self.gitlab_merge_request_payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "iid": '2',
                "last_commit": {
                    "id": self.commit
                },
                "action": "open"
            },
        }
        self.gitlab_payload = {
            'object_kind': GITLAB_PUSH,
            'ref': 'master',
            'before': '95790bf891e76fee5e1747ab589903a6a1f80f22',
            'after': '95790bf891e76fee5e1747ab589903a6a1f80f23',
        }
        self.bitbucket_payload = {
            'push': {
                'changes': [{
                    'new': {
                        'type': 'branch',
                        'name': 'master',
                    },
                    'old': {
                        'type': 'branch',
                        'name': 'master',
                    },
                }],
            },
        }

    def test_webhook_skipped_project(self, trigger_build):
        client = APIClient()
        self.project.skip = True
        self.project.save()

        response = client.post(
            '/api/v2/webhook/github/{}/'.format(
                self.project.slug,
            ),
            self.github_payload,
            format='json',
        )
        self.assertDictEqual(response.data, {'detail': 'This project is currently disabled'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertFalse(trigger_build.called)

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_sync_repository_custom_project_queue(self, sync_repository_task, trigger_build):
        client = APIClient()
        self.project.build_queue = 'specific-build-queue'
        self.project.save()

        headers = {GITHUB_EVENT_HEADER: GITHUB_CREATE}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            self.github_payload,
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        self.assertTrue(resp.data['versions_synced'])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            (latest_version.pk,),
            queue='specific-build-queue',
        )

    def test_github_webhook_for_branches(self, trigger_build):
        """GitHub webhook API."""
        client = APIClient()

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'master'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=self.version, project=self.project)],
        )

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)],
        )

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'refs/heads/master'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=self.version, project=self.project)],
        )

    def test_github_webhook_for_tags(self, trigger_build):
        """GitHub webhook API."""
        client = APIClient()

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'v1.0'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=self.version_tag, project=self.project)],
        )

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'refs/heads/non-existent'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)],
        )

        client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'ref': 'refs/tags/v1.0'},
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=self.version_tag, project=self.project)],
        )

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_github_webhook_no_build_on_delete(self, sync_repository_task, trigger_build):
        client = APIClient()

        payload = {'ref': 'master', 'deleted': True}
        headers = {GITHUB_EVENT_HEADER: GITHUB_PUSH}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_github_create_event(self, sync_repository_task, trigger_build):
        client = APIClient()

        headers = {GITHUB_EVENT_HEADER: GITHUB_CREATE}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            self.github_payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_github_pull_request_opened_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            self.github_pull_request_payload,
            format='json',
            **headers
        )
        # get the created external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name='2')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_github_pull_request_reopened_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        # Update the payload for `reopened` webhook event
        pull_request_number = '5'
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_REOPENED
        payload["number"] = pull_request_number

        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )
        # get the created external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name=pull_request_number)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_github_pull_request_synchronize_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        pull_request_number = '6'
        prev_identifier = '95790bf891e76fee5e1747ab589903a6a1f80f23'
        # create an existing external version for pull request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=pull_request_number,
            identifier=prev_identifier
        )

        # Update the payload for `synchronize` webhook event
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_SYNC
        payload["number"] = pull_request_number

        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )
        # get updated external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name=pull_request_number)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        # `synchronize` webhook event updated the identifier (commit hash)
        self.assertNotEqual(prev_identifier, external_version.identifier)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_github_pull_request_closed_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        pull_request_number = '7'
        identifier = '95790bf891e76fee5e1747ab589903a6a1f80f23'
        # create an existing external version for pull request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=pull_request_number,
            identifier=identifier
        )

        # Update the payload for `closed` webhook event
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_CLOSED
        payload["number"] = pull_request_number
        payload["pull_request"]["head"]["sha"] = identifier

        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )
        external_version = self.project.versions(
            manager=EXTERNAL
        ).filter(verbose_name=pull_request_number)

        # external version should be deleted
        self.assertFalse(external_version.exists())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['version_deleted'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [version.verbose_name])
        core_trigger_build.assert_not_called()

    def test_github_pull_request_no_action(self, trigger_build):
        client = APIClient()

        payload = {
            "number": 2,
            "pull_request": {
                "head": {
                    "sha": "ec26de721c3235aad62de7213c562f8c821"
                }
            }
        }
        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_github_pull_request_opened_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "action": GITHUB_PULL_REQUEST_OPENED,
            "number": 2,
        }
        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )

        self.assertEqual(resp.status_code, 400)

    def test_github_pull_request_closed_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "action": GITHUB_PULL_REQUEST_CLOSED,
            "number": 2,
        }
        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            payload,
            format='json',
            **headers
        )

        self.assertEqual(resp.status_code, 400)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_github_pull_request_event_no_feature_flag(self, trigger_build, core_trigger_build):
        # delete feature flag
        self.feature_flag.delete()

        client = APIClient()

        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            self.github_pull_request_payload,
            format='json',
            **headers
        )
        # get external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).filter(verbose_name='2').first()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')
        core_trigger_build.assert_not_called()
        self.assertFalse(external_version)

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_github_delete_event(self, sync_repository_task, trigger_build):
        client = APIClient()

        headers = {GITHUB_EVENT_HEADER: GITHUB_DELETE}
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            self.github_payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    def test_github_parse_ref(self, trigger_build):
        wh = GitHubWebhookView()

        self.assertEqual(wh._normalize_ref('refs/heads/master'), 'master')
        self.assertEqual(wh._normalize_ref('refs/heads/v0.1'), 'v0.1')
        self.assertEqual(wh._normalize_ref('refs/tags/v0.1'), 'v0.1')
        self.assertEqual(wh._normalize_ref('refs/tags/tag'), 'tag')
        self.assertEqual(wh._normalize_ref('refs/heads/stable/2018'), 'stable/2018')
        self.assertEqual(wh._normalize_ref('refs/tags/tag/v0.1'), 'tag/v0.1')

    def test_github_invalid_webhook(self, trigger_build):
        """GitHub webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/github/{}/'.format(self.project.slug),
            {'foo': 'bar'},
            format='json',
            HTTP_X_GITHUB_EVENT='issues',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_github_invalid_payload(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
        )
        wrong_signature = '1234'
        self.assertNotEqual(integration.secret, wrong_signature)
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: wrong_signature,
        }
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            self.github_payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.data['detail'],
            GitHubWebhookView.invalid_payload_msg
        )

    def test_github_valid_payload(self, trigger_build):
        client = APIClient()
        payload = '{"ref":"master"}'
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
        )
        digest = GitHubWebhookView.get_digest(
            integration.secret,
            payload,
        )
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: 'sha1=' + digest,
        }
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            json.loads(payload),
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 200)

    def test_github_empty_signature(self, trigger_build):
        client = APIClient()
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: '',
        }
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
        )
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            self.github_payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.data['detail'],
            GitHubWebhookView.invalid_payload_msg
        )

    def test_github_skip_signature_validation(self, trigger_build):
        client = APIClient()
        payload = '{"ref":"master"}'
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
            secret=None,
        )
        self.assertFalse(integration.secret)
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: 'skipped',
        }
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            json.loads(payload),
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 200)

    def test_github_sync_on_push_event(self, trigger_build):
        """Sync if the webhook doesn't have the create/delete events, but we recieve a push event with created/deleted."""
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data={
                'events': [],
            },
            secret=None,
        )

        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
        }
        payload = {
            'ref': 'master',
            'created': True,
            'deleted': False,
        }
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
            **headers
        )
        self.assertTrue(resp.json()['versions_synced'])

    def test_github_dont_trigger_double_sync(self, trigger_build):
        """Don't trigger a sync twice if the webhook has the create/delete events."""
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
            provider_data={
                'events': [
                    GITHUB_CREATE,
                    GITHUB_DELETE,
                ],
            },
            secret=None,
        )

        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
        }
        payload = {
            'ref': 'master',
            'created': True,
            'deleted': False,
        }
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
            **headers
        )
        self.assertFalse(resp.json()['versions_synced'])

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_CREATE,
        }
        payload = {'ref': 'master'}
        resp = client.post(
            reverse(
                'api_webhook_github',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
            **headers
        )
        self.assertTrue(resp.json()['versions_synced'])

    def test_gitlab_webhook_for_branches(self, trigger_build):
        """GitLab webhook API."""
        client = APIClient()
        client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        trigger_build.assert_called_with(
            force=True, version=mock.ANY, project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref='non-existent',
        )
        client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        trigger_build.assert_not_called()

    def test_gitlab_webhook_for_tags(self, trigger_build):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            ref='v1.0',
        )
        client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        trigger_build.assert_called_with(
            force=True, version=self.version_tag, project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref='refs/tags/v1.0',
        )
        client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        trigger_build.assert_called_with(
            force=True, version=self.version_tag, project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref='refs/heads/non-existent',
        )
        client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        trigger_build.assert_not_called()

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_gitlab_push_hook_creation(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            before=GITLAB_NULL_HASH,
            after='95790bf891e76fee5e1747ab589903a6a1f80f22',
        )
        resp = client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_gitlab_push_hook_deletion(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            before='95790bf891e76fee5e1747ab589903a6a1f80f22',
            after=GITLAB_NULL_HASH,
        )
        resp = client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_gitlab_tag_push_hook_creation(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            before=GITLAB_NULL_HASH,
            after='95790bf891e76fee5e1747ab589903a6a1f80f22',
        )
        resp = client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_gitlab_tag_push_hook_deletion(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            before='95790bf891e76fee5e1747ab589903a6a1f80f22',
            after=GITLAB_NULL_HASH,
        )
        resp = client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            self.gitlab_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    def test_gitlab_invalid_webhook(self, trigger_build):
        """GitLab webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/gitlab/{}/'.format(self.project.slug),
            {'object_kind': 'pull_request'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_gitlab_invalid_payload(self, trigger_build):
        client = APIClient()
        wrong_secret = '1234'
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITLAB_WEBHOOK,
        )
        self.assertNotEqual(integration.secret, wrong_secret)
        headers = {
            GITLAB_TOKEN_HEADER: wrong_secret,
        }
        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            self.gitlab_payload,
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.data['detail'],
            GitLabWebhookView.invalid_payload_msg
        )

    def test_gitlab_valid_payload(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITLAB_WEBHOOK,
        )
        headers = {
            GITLAB_TOKEN_HEADER: integration.secret,
        }
        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            {'object_kind': 'pull_request'},
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 200)

    def test_gitlab_empty_token(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITLAB_WEBHOOK,
        )
        headers = {
            GITLAB_TOKEN_HEADER: '',
        }
        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            {'object_kind': 'pull_request'},
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.data['detail'],
            GitLabWebhookView.invalid_payload_msg
        )

    def test_gitlab_skip_token_validation(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITLAB_WEBHOOK,
            secret=None,
        )
        self.assertFalse(integration.secret)
        headers = {
            GITLAB_TOKEN_HEADER: 'skipped',
        }
        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            {'object_kind': 'pull_request'},
            format='json',
            **headers
        )
        self.assertEqual(resp.status_code, 200)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_open_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            self.gitlab_merge_request_payload,
            format='json',
        )
        # get the created external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name='2')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_reopen_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        # Update the payload for `reopen` webhook event
        merge_request_number = '5'
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_REOPEN
        payload["object_attributes"]["iid"] = merge_request_number

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )
        # get the created external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name=merge_request_number)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_update_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = '6'
        prev_identifier = '95790bf891e76fee5e1747ab589903a6a1f80f23'
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=prev_identifier
        )

        # Update the payload for merge request `update` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_UPDATE
        payload["object_attributes"]["iid"] = merge_request_number

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )
        # get updated external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).get(verbose_name=merge_request_number)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            force=True, project=self.project,
            version=external_version, commit=self.commit
        )
        # `update` webhook event updated the identifier (commit hash)
        self.assertNotEqual(prev_identifier, external_version.identifier)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_close_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = '7'
        identifier = '95790bf891e76fee5e1747ab589903a6a1f80f23'
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=identifier
        )

        # Update the payload for `closed` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_CLOSE
        payload["object_attributes"]["iid"] = merge_request_number
        payload["object_attributes"]["last_commit"]["id"] = identifier

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )
        external_version = self.project.versions(
            manager=EXTERNAL
        ).filter(verbose_name=merge_request_number)

        # external version should be deleted
        self.assertFalse(external_version.exists())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['version_deleted'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [version.verbose_name])
        core_trigger_build.assert_not_called()

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_merge_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = '8'
        identifier = '95790bf891e76fee5e1747ab589903a6a1f80f23'
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=identifier
        )

        # Update the payload for `merge` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_MERGE
        payload["object_attributes"]["iid"] = merge_request_number
        payload["object_attributes"]["last_commit"]["id"] = identifier

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )
        external_version = self.project.versions(
            manager=EXTERNAL
        ).filter(verbose_name=merge_request_number)

        # external version should be deleted
        self.assertFalse(external_version.exists())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['version_deleted'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [version.verbose_name])
        core_trigger_build.assert_not_called()

    def test_gitlab_merge_request_no_action(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "iid": 2,
                "last_commit": {
                    "id": self.commit
                },
            },
        }

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_gitlab_merge_request_open_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "action": GITLAB_MERGE_REQUEST_CLOSE
            },
        }
        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )

        self.assertEqual(resp.status_code, 400)

    def test_gitlab_merge_request_close_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "action": GITLAB_MERGE_REQUEST_CLOSE
            },
        }

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            payload,
            format='json',
        )

        self.assertEqual(resp.status_code, 400)

    @mock.patch('readthedocs.core.utils.trigger_build')
    def test_gitlab_merge_request_event_no_feature_flag(self, trigger_build, core_trigger_build):
        # delete feature flag
        self.feature_flag.delete()

        client = APIClient()

        resp = client.post(
            reverse(
                'api_webhook_gitlab',
                kwargs={'project_slug': self.project.slug}
            ),
            self.gitlab_merge_request_payload,
            format='json',
        )
        # get external version
        external_version = self.project.versions(
            manager=EXTERNAL
        ).filter(verbose_name='2').first()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')
        core_trigger_build.assert_not_called()
        self.assertFalse(external_version)

    def test_bitbucket_webhook(self, trigger_build):
        """Bitbucket webhook API."""
        client = APIClient()
        client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
            self.bitbucket_payload,
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)],
        )
        client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
            {
                'push': {
                    'changes': [
                        {
                            'new': {'name': 'non-existent'},
                            'old': {'name': 'master'},
                        },
                    ],
                },
            },
            format='json',
        )
        trigger_build.assert_has_calls(
            [mock.call(force=True, version=mock.ANY, project=self.project)],
        )

        trigger_build_call_count = trigger_build.call_count
        client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
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
        self.assertEqual(trigger_build_call_count, trigger_build.call_count)

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_bitbucket_push_hook_creation(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.bitbucket_payload['push']['changes'][0]['old'] = None
        resp = client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
            self.bitbucket_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    @mock.patch('readthedocs.core.views.hooks.sync_repository_task')
    def test_bitbucket_push_hook_deletion(
            self, sync_repository_task, trigger_build,
    ):
        client = APIClient()
        self.bitbucket_payload['push']['changes'][0]['new'] = None
        resp = client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
            self.bitbucket_payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['build_triggered'])
        self.assertEqual(resp.data['project'], self.project.slug)
        self.assertEqual(resp.data['versions'], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with((latest_version.pk,))

    def test_bitbucket_invalid_webhook(self, trigger_build):
        """Bitbucket webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/bitbucket/{}/'.format(self.project.slug),
            {'foo': 'bar'}, format='json', HTTP_X_EVENT_KEY='pull_request',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['detail'], 'Unhandled webhook event')

    def test_generic_api_fails_without_auth(self, trigger_build):
        client = APIClient()
        resp = client.post(
            '/api/v2/webhook/generic/{}/'.format(self.project.slug),
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
            '/api/v2/webhook/{}/{}/'.format(
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
            '/api/v2/webhook/{}/{}/'.format(
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
            '/api/v2/webhook/generic/{}/'.format(self.project.slug),
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
            project=self.project, integration_type=Integration.API_WEBHOOK,
        )
        self.assertIsNotNone(integration.token)
        resp = client.post(
            '/api/v2/webhook/{}/{}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])

    def test_webhook_doesnt_build_latest_if_is_deactivated(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        latest_version.active = False
        latest_version.save()

        default_branch = self.project.versions.get(slug='master')
        default_branch.active = False
        default_branch.save()

        resp = client.post(
            '/api/v2/webhook/{}/{}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token, 'branches': default_branch.slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['build_triggered'])
        trigger_build.assert_not_called()

    def test_webhook_builds_only_master(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        latest_version.active = False
        latest_version.save()

        default_branch = self.project.versions.get(slug='master')

        self.assertFalse(latest_version.active)
        self.assertTrue(default_branch.active)

        resp = client.post(
            '/api/v2/webhook/{}/{}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token, 'branches': default_branch.slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['versions'], ['master'])

    def test_webhook_build_latest_and_master(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        default_branch = self.project.versions.get(slug='master')

        self.assertTrue(latest_version.active)
        self.assertTrue(default_branch.active)

        resp = client.post(
            '/api/v2/webhook/{}/{}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token, 'branches': default_branch.slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(set(resp.data['versions']), {'latest', 'master'})

    def test_webhook_build_another_branch(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        version_v1 = self.project.versions.get(slug='v1.0')

        self.assertTrue(version_v1.active)

        resp = client.post(
            '/api/v2/webhook/{}/{}/'.format(
                self.project.slug,
                integration.pk,
            ),
            {'token': integration.token, 'branches': version_v1.slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['build_triggered'])
        self.assertEqual(resp.data['versions'], ['v1.0'])


class APIVersionTests(TestCase):
    fixtures = ['eric', 'test_data']
    maxDiff = None  # So we get an actual diff when it fails

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
                'analytics_disabled': False,
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
                'environment_variables': {},
                'enable_epub_build': True,
                'enable_pdf_build': True,
                'features': ['allow_deprecated_webhooks'],
                'has_valid_clone': False,
                'has_valid_webhook': False,
                'id': 6,
                'install_project': False,
                'language': 'en',
                'max_concurrent_builds': None,
                'name': 'Pip',
                'programming_language': 'words',
                'python_interpreter': 'python3',
                'repo': 'https://github.com/pypa/pip',
                'repo_type': 'git',
                'requirements_file': None,
                'show_advertising': True,
                'skip': False,
                'slug': 'pip',
                'use_system_packages': False,
                'users': [1],
                'urlconf': None,
            },
            'privacy_level': 'public',
            'downloads': {},
            'identifier': '2404a34eba4ee9c48cc8bc4055b99a48354f4950',
            'slug': '0.8',
            'has_epub': False,
            'has_htmlzip': False,
            'has_pdf': False,
            'documentation_type': 'sphinx',
        }

        self.assertDictEqual(
            resp.data,
            version_data,
        )

    def test_get_active_versions(self):
        """Test the full response of
        ``/api/v2/version/?project__slug=pip&active=true``"""
        pip = Project.objects.get(slug='pip')

        data = QueryDict('', mutable=True)
        data.update({
            'project__slug': pip.slug,
            'active': 'true',
        })
        url = '{base_url}?{querystring}'.format(
            base_url=reverse('version-list'),
            querystring=data.urlencode(),
        )

        resp = self.client.get(url, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], pip.versions.filter(active=True).count())

        # Do the same thing for inactive versions
        data.update({
            'project__slug': pip.slug,
            'active': 'false',
        })
        url = '{base_url}?{querystring}'.format(
            base_url=reverse('version-list'),
            querystring=data.urlencode(),
        )

        resp = self.client.get(url, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], pip.versions.filter(active=False).count())

    def test_modify_version(self):
        pip = Project.objects.get(slug='pip')
        version = pip.versions.get(slug='0.8')

        data = {
            'pk': version.pk,
        }
        resp = self.client.patch(
            reverse('version-detail', kwargs=data),
            data=json.dumps({'built': False, 'has_pdf': True}),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic {}'.format(eric_auth),  # Eric is staff
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['built'], False)
        self.assertEqual(resp.data['has_pdf'], True)
        self.assertEqual(resp.data['has_epub'], False)
        self.assertEqual(resp.data['has_htmlzip'], False)


class TaskViewsTests(TestCase):

    def test_get_status_data(self):
        data = get_status_data(
            'public_task_exception',
            'SUCCESS',
            {'data': 'public'},
            'Something bad happened',
        )
        self.assertEqual(
            data, {
                'name': 'public_task_exception',
                'data': {'data': 'public'},
                'started': True,
                'finished': True,
                'success': False,
                'error': 'Something bad happened',
            },
        )
