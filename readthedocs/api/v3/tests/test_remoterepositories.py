from django.urls import reverse

import django_dynamic_fixture as fixture

from .mixins import APIEndpointMixin
from readthedocs.oauth.models import RemoteRepository


class ProjectsEndpointTests(APIEndpointMixin):

    def setUp(self):
        super().setUp()

        self.remote_repository = fixture.get(
            RemoteRepository,
            pub_date=self.created,
            modified_date=self.modified,
            avatar_url="https://avatars3.githubusercontent.com/u/test-rtd?v=4",
            clone_url="https://github.com/rtd/project.git",
            description="This is a test project.",
            full_name="rtd/project",
            html_url="https://github.com/rtd/project",
            name="project",
            ssh_url="git@github.com:rtd/project.git",
            vcs="git",
            users=[self.me]
        )

    def test_projects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse('remoterepositories-list')
        )
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict('remoterepositories-list'),
        )
