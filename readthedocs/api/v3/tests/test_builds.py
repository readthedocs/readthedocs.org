from unittest import mock

from django.test import override_settings
from django.urls import reverse

from readthedocs.builds.constants import EXTERNAL
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

    def test_external_version_projects_versions_builds_list_post(self):
        """Build starts using last commit against external version."""
        self.version.type = EXTERNAL
        self.build.commit = "d4e5f6"
        self.version.save()
        self.build.save()
        url = reverse(
            "projects-versions-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_version__slug": self.version.slug,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertEqual(self.project.builds.count(), 1)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.project.builds.count(), 2)

        response_json = response.json()
        response_json["build"]["created"] = "2019-04-29T14:00:00Z"
        expected = self._get_response_dict("projects-versions-builds-list_POST")
        expected["build"]["commit"] = "d4e5f6"
        expected["version"]["type"] = "external"
        expected["version"]["urls"][
            "documentation"
        ] = "http://project--v1.0.external-builds.readthedocs.io/en/v1.0/"
        expected["version"]["urls"]["vcs"] = "https://github.com/rtfd/project/pull/v1.0"
        self.assertDictEqual(response_json, expected)

    def test_projects_builds_notifications_list(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
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
            self._get_response_dict("projects-builds-notifications-list"),
        )

    def test_projects_builds_notifications_list_other_user(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_projects_builds_notifications_list_post(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertEqual(self.project.builds.count(), 1)
        response = self.client.post(url)

        # We don't allow POST on this endpoint
        self.assertEqual(response.status_code, 405)

    def test_projects_builds_notifitications_detail(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
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
            self._get_response_dict("projects-builds-notifications-detail"),
        )

    def test_projects_builds_notifitications_detail_other_user(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_projects_builds_notifitications_detail_post(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
            },
        )
        data = {"state": "read"}

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.build.notifications.first().state, "read")
