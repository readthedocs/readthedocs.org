import datetime
import mock
import json
from pathlib import Path

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


class APIEndpointTests(TestCase):

    fixtures = []

    def setUp(self):
        created = make_aware(datetime.datetime(2019, 4, 29, 10, 0, 0))
        modified = make_aware(datetime.datetime(2019, 4, 29, 12, 0, 0))

        self.me = fixture.get(
            User,
            date_joined=created,
            username='testuser',
            projects=[],
        )
        self.token = fixture.get(Token, key='me', user=self.me)
        # Defining all the defaults helps to avoid creating ghost / unwanted
        # objects (like a Project for translations/subprojects)
        self.project = fixture.get(
            Project,
            pub_date=created,
            modified_date=modified,
            description='Project description',
            repo='https://github.com/rtfd/project',
            project_url='http://project.com',
            name='project',
            slug='project',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        for tag in ('tag', 'project', 'test'):
            self.project.tags.add(tag)

        self.redirect = fixture.get(
            Redirect,
            create_dt=created,
            update_dt=modified,
            from_url='/docs/',
            to_url='/documentation/',
            redirect_type='page',
            project=self.project,
        )

        self.subproject = fixture.get(
            Project,
            pub_date=created,
            modified_date=modified,
            description='SubProject description',
            repo='https://github.com/rtfd/subproject',
            project_url='http://subproject.com',
            name='subproject',
            slug='subproject',
            related_projects=[],
            main_language_project=None,
            users=[],
            versions=[],
        )
        # self.translation = fixture.get(Project, slug='translation')

        self.project.add_subproject(self.subproject)
        # self.project.add_translation(self.translation)

        self.version = fixture.get(
            Version,
            slug='v1.0',
            verbose_name='v1.0',
            identifier='a1b2c3',
            project=self.project,
            active=True,
            built=True,
            type='tag',
        )

        self.build = fixture.get(
            Build,
            date=created,
            type='html',
            state='finished',
            error='',
            success=True,
            _config = {'property': 'test value'},
            version=self.version,
            project=self.project,
            builder='builder01',
            commit='a1b2c3',
            length=60,
        )

        self.other = fixture.get(User, projects=[])
        self.others_token = fixture.get(Token, key='other', user=self.other)
        self.others_project = fixture.get(
            Project,
            slug='others_project',
            related_projects=[],
            main_language_project=None,
            users=[self.other],
            versions=[],
        )

        self.client = APIClient()

    def tearDown(self):
        # Cleanup cache to avoid throttling on tests
        cache.clear()

    def _get_response_dict(self, view_name):
        filename = Path(__file__).absolute().parent / 'responses' / f'{view_name}.json'
        return json.load(open(filename))

    def assertDictEqual(self, d1, d2):
        """
        Show the differences between the dicts in a human readable way.

        It's just a helper for debugging API responses.
        """
        import datadiff
        return super().assertDictEqual(d1, d2, datadiff.diff(d1, d2))

    def test_projects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse('projects-list'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-list'),
        )

    def test_own_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.project.slug,
                }),
            {
                'expand': (
                    'active_versions,'
                    'active_versions.last_build,'
                    'active_versions.last_build.config'
                ),
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-detail'),
        )

    def test_projects_superproject(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-superproject',
                kwargs={
                    'project_slug': self.subproject.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-superproject'),
        )

    def test_projects_subprojects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_superprojects__parent__slug': self.project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-subprojects-list'),
        )

    def test_others_projects_builds_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-builds-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 403)

    def test_others_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

    def test_unauthed_others_projects_detail(self):
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': 'nonexistent',
                }),

        )
        self.assertEqual(response.status_code, 404)

    def test_projects_versions_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

    def test_others_projects_versions_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 403)

    def test_projects_versions_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'version_slug': 'v1.0',
                }),

        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-versions-detail'),
        )

    def test_nonexistent_project_version_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': 'nonexistent',
                    'version_slug': 'latest',
                }),

        )
        self.assertEqual(response.status_code, 404)

    def test_projects_builds_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-builds-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
        )
        self.assertEqual(response.status_code, 200)

    def test_projects_builds_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-builds-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'build_pk': self.build.pk,
                }),
        )
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-builds-detail'),
        )

    def test_projects_versions_builds_list_post(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(self.project.builds.count(), 1)
        response = self.client.post(
            reverse(
                'projects-versions-builds-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'parent_lookup_version__slug': self.version.slug,
                }),
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.project.builds.count(), 2)

        response_json = response.json()
        response_json['build']['created'] = '2019-04-29T14:00:00Z'
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-versions-builds-list_POST'),
        )

    def test_projects_versions_detail_unique(self):
        second_project = fixture.get(
            Project,
            name='second project',
            slug='second-project',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        second_version = fixture.get(
            Version,
            slug=self.version.slug,
            verbose_name=self.version.verbose_name,
            identifier='a1b2c3',
            project=second_project,
            active=True,
            built=True,
            type='tag',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'version_slug': self.version.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)


    def test_unauthed_projects_redirects_list(self):
        response = self.client.get(
            reverse(
                'projects-redirects-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_redirects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-redirects-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-redirects-list'),
        )

    def test_unauthed_projects_redirects_detail(self):
        response = self.client.get(
            reverse(
                'projects-redirects-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'redirect_pk': self.redirect.pk,
                }),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_redirects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-redirects-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'redirect_pk': self.redirect.pk,
                }),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-redirects-detail'),
        )

    def test_unauthed_projects_redirects_list_post(self):
        data = {}

        response = self.client.post(
            reverse(
                'projects-redirects-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),
            data,
        )
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(
            reverse(
                'projects-redirects-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),
            data,
        )
        self.assertEqual(response.status_code, 403)

    def test_projects_redirects_list_post(self):
        data = {
            'from_url': '/page/',
            'to_url': '/another/',
            'type': 'page',
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(
            reverse(
                'projects-redirects-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
            data,
        )
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        response_json['created'] = '2019-04-29T10:00:00Z'
        response_json['modified'] = '2019-04-29T12:00:00Z'
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-redirects-list_POST'),
        )

    def test_projects_redirects_detail_put(self):
        data = {
            'from_url': '/changed/',
            'to_url': '/toanother/',
            'type': 'page',
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(
            reverse(
                'projects-redirects-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'redirect_pk': self.redirect.pk,
                }),
            data,
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        response_json['modified'] = '2019-04-29T12:00:00Z'
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-redirects-detail_PUT'),
        )

    def test_projects_redirects_detail_delete(self):
        self.assertEqual(self.project.redirects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(
            reverse(
                'projects-redirects-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'redirect_pk': self.redirect.pk,
                }),
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.redirects.count(), 0)


    @mock.patch('readthedocs.api.v3.views.trigger_initial_build')
    @mock.patch('readthedocs.api.v3.views.project_import')
    def test_import_project(self, project_import, trigger_initial_build):
        data = {
            'name': 'Test Project',
            'repository': {
                'url': 'https://github.com/rtfd/template',
                'type': 'git',
            },
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('projects-list'), data)
        self.assertEqual(response.status_code, 201)

        query = Project.objects.filter(slug='test-project')
        self.assertTrue(query.exists())

        project = query.first()
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.slug, 'test-project')
        self.assertEqual(project.repo, 'https://github.com/rtfd/template')
        self.assertEqual(project.language, 'en')
        self.assertIn(self.me, project.users.all())

        # Signal sent
        project_import.send.assert_has_calls(
            [
                mock.call(
                    sender=project,
                    request=mock.ANY,
                ),
            ],
        )

        # Build triggered
        trigger_initial_build.assert_has_calls(
            [
                mock.call(
                    project,
                    self.me,
                ),
            ],
        )

        response_json = response.json()
        response_json['created'] = '2019-04-29T14:00:00Z'
        response_json['modified'] = '2019-04-29T14:00:00Z'
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-list_POST'),
        )
