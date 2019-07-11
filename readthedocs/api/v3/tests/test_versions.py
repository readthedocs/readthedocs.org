from .mixins import APIEndpointMixin
from django.urls import reverse

import django_dynamic_fixture as fixture

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class VerionsEndpointTests(APIEndpointMixin):

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
