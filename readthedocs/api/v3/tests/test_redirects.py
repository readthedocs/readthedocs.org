from .mixins import APIEndpointMixin
from django.urls import reverse


class RedirectsEndpointTests(APIEndpointMixin):

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
