from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

import django_dynamic_fixture as fixture
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class APIEndpointTests(TestCase):

    def setUp(self):

        self.me = fixture.get(User)
        self.token = fixture.get(Token, key='me', user=self.me)
        self.project = fixture.get(Project, slug='project', users=[self.me])
        self.subproject = fixture.get(Project, slug='subproject')
        # self.translation = fixture.get(Project, slug='translation')

        self.project.add_subproject(self.subproject)
        # self.project.add_translation(self.translation)

        self.version = fixture.get(Version, slug='v1.0', project=self.project)

        self.other = fixture.get(User)
        self.others_token = fixture.get(Token, key='other', user=self.other)
        self.others_project = fixture.get(Project, slug='others_project', users=[self.other])

        self.client = APIClient()

    def test_list_my_projects(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse('projects-list'),
        )
        self.assertEqual(response.status_code, 200)

    def test_subprojects(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_superprojects__parent__slug': self.project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

    def test_detail_own_project(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

    def test_detail_others_project(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 200)

    def test_unauthed_detail_others_project(self):
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                }),

        )
        self.assertEqual(response.status_code, 401)

    def test_detail_nonexistent_project(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': 'nonexistent',
                }),

        )
        self.assertEqual(response.status_code, 404)

    def test_detail_version_of_project(self):
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

    def test_detail_version_of_nonexistent_project(self):
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
