from .mixins import APIEndpointMixin
from django.urls import reverse
import django_dynamic_fixture as fixture

from readthedocs.projects.models import Project


class SubprojectsEndpointTests(APIEndpointMixin):

    def setUp(self):
        super().setUp()
        self._create_subproject()

    def test_projects_subprojects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-subprojects-list'),
        )

    def test_projects_subprojects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-subprojects-detail',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                    'alias_slug': self.project_relationship.alias,
                }),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-subprojects-detail'),
        )

    def test_projects_subprojects_list_post(self):
        newproject = self._create_new_project()
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': newproject.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                },
            ),
            data,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.subprojects.count(), 2)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-subprojects-list_POST'),
        )

    def test_projects_subprojects_list_post_with_others_as_child(self):
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': self.others_project.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_with_subproject_of_itself(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': newproject.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Project can not be subproject of itself',
            response.json()['non_field_errors'],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_with_child_already_superproject(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.assertTrue(self.project.subprojects.exists())
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': self.project.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Child is already a superproject',
            response.json()['child'],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_with_child_already_subproject(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.assertTrue(self.subproject.superprojects.exists())
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': self.subproject.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Child is already a subproject of another project',
            response.json()['child'],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_nested_subproject(self):
        newproject = self._create_new_project()
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': newproject.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.subproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'Subproject nesting is not supported',
            response.json()['non_field_errors'],
        )
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_unique_alias(self):
        newproject = self._create_new_project()
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': newproject.slug,
            'alias': 'subproject',  # this alias is already set for another subproject
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'A subproject with this alias already exists',
            response.json()['alias'],
        )
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_with_others_as_parent(self):
        self.assertEqual(self.others_project.subprojects.count(), 0)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            'child': self.project.slug,
            'alias': 'subproject-alias',
        }
        response = self.client.post(
            reverse(
                'projects-subprojects-list',
                kwargs={
                    'parent_lookup_parent__slug': self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.others_project.subprojects.count(), 0)

    def test_projects_subprojects_detail_delete(self):
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(
            reverse(
                'projects-subprojects-detail',
                kwargs={
                    'parent_lookup_parent__slug': self.project.slug,
                    'alias_slug': self.project_relationship.alias,
                },
            ),
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.subprojects.count(), 0)

    def test_projects_subprojects_detail_delete_others_project(self):
        newproject =  self._create_new_project()
        project_relationship = self.others_project.add_subproject(newproject)
        self.assertEqual(self.others_project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(
            reverse(
                'projects-subprojects-detail',
                kwargs={
                    'parent_lookup_parent__slug': self.others_project.slug,
                    'alias_slug': project_relationship.alias,
                },
            ),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.project.subprojects.count(), 1)
