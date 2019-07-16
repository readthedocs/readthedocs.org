from .mixins import APIEndpointMixin
from django.urls import reverse

import django_dynamic_fixture as fixture
from readthedocs.projects.models import EnvironmentVariable


class EnvironmentVariablessEndpointTests(APIEndpointMixin):

    def setUp(self):
        super().setUp()

        self.environmentvariable = fixture.get(
            EnvironmentVariable,
            created=self.created,
            modified=self.modified,
            project=self.project,
            name='ENVVAR',
            value='a1b2c3',
        )

    def test_unauthed_projects_environmentvariables_list(self):
        response = self.client.get(
            reverse(
                'projects-environmentvariables-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_environmentvariables_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-environmentvariables-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-environmentvariables-list'),
        )

    def test_unauthed_projects_environmentvariables_detail(self):
        response = self.client.get(
            reverse(
                'projects-environmentvariables-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'environmentvariable_pk': self.environmentvariable.pk,
                }),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_environmentvariables_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-environmentvariables-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'environmentvariable_pk': self.environmentvariable.pk,
                }),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-environmentvariables-detail'),
        )

    def test_unauthed_projects_environmentvariables_list_post(self):
        data = {}

        response = self.client.post(
            reverse(
                'projects-environmentvariables-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),
            data,
        )
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(
            reverse(
                'projects-environmentvariables-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                }),
            data,
        )
        self.assertEqual(response.status_code, 403)

    def test_projects_environmentvariables_list_post(self):
        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        data = {
            'name': 'NEWENVVAR',
            'value': 'c3b2a1',
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(
            reverse(
                'projects-environmentvariables-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                }),
            data,
        )
        self.assertEqual(self.project.environmentvariable_set.count(), 2)
        self.assertEqual(response.status_code, 201)

        environmentvariable = self.project.environmentvariable_set.get(name='NEWENVVAR')
        self.assertEqual(environmentvariable.value, 'c3b2a1')

        response_json = response.json()
        response_json['created'] = '2019-04-29T10:00:00Z'
        response_json['modified'] = '2019-04-29T12:00:00Z'
        self.assertDictEqual(
            response_json,
            self._get_response_dict('projects-environmentvariables-list_POST'),
        )

    def test_projects_environmentvariables_detail_delete(self):
        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(
            reverse(
                'projects-environmentvariables-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'environmentvariable_pk': self.environmentvariable.pk,
                }),
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.environmentvariable_set.count(), 0)
