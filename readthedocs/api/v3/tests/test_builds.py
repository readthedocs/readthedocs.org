from unittest import mock

from django.test import override_settings
from django.urls import reverse

from readthedocs.subscriptions.constants import TYPE_CONCURRENT_BUILDS
from readthedocs.subscriptions.products import RTDProductFeature

from .mixins import APIEndpointMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
    RTD_DEFAULT_FEATURES=dict(
        [RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=4).to_item()]
    ),
)
@mock.patch("readthedocs.projects.tasks.builds.update_docs_task", mock.MagicMock())
class BuildsEndpointTests(APIEndpointMixin):
    def test_projects_builds_list(self):
        url = reverse(
            "projects-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_projects_builds_detail(self):
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-builds-detail"),
        )

    def test_projects_versions_builds_list_post(self):
        url = reverse(
            "projects-versions-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_version__slug": self.version.slug,
            },
        )

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertEqual(self.project.builds.count(), 1)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.project.builds.count(), 2)

        response_json = response.json()
        response_json["build"]["created"] = "2019-04-29T14:00:00Z"
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-versions-builds-list_POST"),
        )
