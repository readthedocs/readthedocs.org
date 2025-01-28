from django.urls import reverse

from allauth.socialaccount.models import SocialAccount
import django_dynamic_fixture as fixture

from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
)
from .mixins import APIEndpointMixin


class RemoteOrganizationEndpointTests(APIEndpointMixin):
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
        social_account = fixture.get(SocialAccount, user=self.me, provider=GITHUB)
        fixture.get(
            RemoteOrganizationRelation,
            remote_organization=self.remote_organization,
            user=self.me,
            account=social_account,
        )

    def test_remote_organization_list(self):
        url = reverse("remoteorganizations-list")

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("remoteorganizations-list"),
        )

    def test_remote_organization_list_name_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("remoteorganizations-list"), {"name": "Read"}
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertEqual(len(response_data["results"]), 1)
        self.assertDictEqual(
            response_data,
            self._get_response_dict("remoteorganizations-list"),
        )
