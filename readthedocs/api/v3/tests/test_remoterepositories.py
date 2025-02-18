import django_dynamic_fixture as fixture
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse

from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.projects.constants import REPO_TYPE_GIT

from .mixins import APIEndpointMixin


class RemoteRepositoryEndpointTests(APIEndpointMixin):
    def setUp(self):
        super().setUp()

        self.remote_organization = fixture.get(
            RemoteOrganization,
            created=self.created,
            modified=self.modified,
            avatar_url="https://avatars.githubusercontent.com/u/366329?v=4",
            name="Read the Docs",
            slug="readthedocs",
            url="https://github.com/readthedocs",
            vcs_provider=GITHUB,
        )

        self.remote_repository = fixture.get(
            RemoteRepository,
            organization=self.remote_organization,
            created=self.created,
            modified=self.modified,
            avatar_url="https://avatars3.githubusercontent.com/u/test-rtd?v=4",
            clone_url="https://github.com/rtd/project.git",
            description="This is a test project.",
            full_name="rtd/project",
            html_url="https://github.com/rtd/project",
            name="project",
            ssh_url="git@github.com:rtd/project.git",
            vcs=REPO_TYPE_GIT,
            vcs_provider=GITHUB,
            default_branch="master",
            private=False,
        )
        self.remote_repository.projects.add(self.project)

        social_account = fixture.get(SocialAccount, user=self.me, provider=GITHUB)
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=self.remote_repository,
            user=self.me,
            account=social_account,
            admin=True,
        )
        fixture.get(
            RemoteOrganizationRelation,
            remote_organization=self.remote_organization,
            user=self.me,
            account=social_account,
        )

    def test_remote_repository_list(self):
        url = reverse("remoterepositories-list")
        data = {"expand": ["remote_organization"]}

        self.client.logout()
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("remoterepositories-list"),
        )

    def test_remote_repository_list_name_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("remoterepositories-list"),
            {"expand": ["remote_organization"], "name": "proj"},
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data["results"]), 1)

        self.assertDictEqual(
            response_data,
            self._get_response_dict("remoterepositories-list"),
        )

    def test_remote_repository_list_full_name_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("remoterepositories-list"),
            {"expand": ["remote_organization"], "full_name": "proj"},
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data["results"]), 1)

        self.assertDictEqual(
            response_data,
            self._get_response_dict("remoterepositories-list"),
        )
