from .mixins import APIEndpointMixin
from django.urls import reverse

from readthedocs.projects.models import Project


class ProjectsEndpointTests(APIEndpointMixin):

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
                },
            ),
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
                },
            ),
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
                },
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_others_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthed_others_projects_detail(self):
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': self.others_project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-detail',
                kwargs={
                    'project_slug': 'nonexistent',
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_import_project(self):
        data = {
            'name': 'Test Project',
            'repository': {
                'url': 'https://github.com/rtfd/template',
                'type': 'git',
            },
            'homepage': 'http://template.readthedocs.io/',
            'programming_language': 'py',
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
        self.assertEqual(project.programming_language, 'py')
        self.assertEqual(project.privacy_level, 'public')
        self.assertEqual(project.project_url, 'http://template.readthedocs.io/')
        self.assertIn(self.me, project.users.all())
        self.assertEqual(project.builds.count(), 1)

        response_json = response.json()
        response_json['created'] = '2019-04-29T10:00:00Z'
        response_json['modified'] = '2019-04-29T12:00:00Z'

    def test_import_project_with_extra_fields(self):
        data = {
            'name': 'Test Project',
            'repository': {
                'url': 'https://github.com/rtfd/template',
                'type': 'git',
            },
            'default_version': 'v1.0',  # ignored: field not allowed
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
        self.assertNotEqual(project.default_version, 'v1.0')
        self.assertIn(self.me, project.users.all())
