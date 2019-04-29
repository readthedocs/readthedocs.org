import datetime
import json

from pathlib import Path


from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

import django_dynamic_fixture as fixture
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.models import Version, Build
from readthedocs.projects.models import Project


class APIEndpointTests(TestCase):

    fixtures = []

    def setUp(self):

        self.me = fixture.get(User, projects=[])
        self.token = fixture.get(Token, key='me', user=self.me)
        # Defining all the defaults helps to avoid creating ghost / unwanted
        # objects (like a Project for translations/subprojects)
        self.project = fixture.get(
            Project,
            pub_date=datetime.datetime(2019, 4, 29, 10, 0, 0),
            modified_date=datetime.datetime(2019, 4, 29, 12, 0, 0),
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

        self.subproject = fixture.get(
            Project,
            pub_date=datetime.datetime(2019, 4, 29, 10, 0, 0),
            modified_date=datetime.datetime(2019, 4, 29, 12, 0, 0),
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
            date=datetime.datetime(2019, 4, 29, 10, 0, 0),
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

    def test_others_projects_users_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-users-list',
                kwargs={
                    'parent_lookup_projects__slug': self.others_project.slug,
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
