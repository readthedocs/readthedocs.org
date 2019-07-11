from .mixins import APIEndpointMixin
from django.urls import reverse


class BuildsEndpointTests(APIEndpointMixin):

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
