from unittest import mock

from django.test import override_settings
from django.urls import reverse

from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.constants import PRIVATE, PUBLIC
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
    def test_projects_builds_list_anonymous_user(self):
        url = reverse(
            "projects-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-builds-list")
        expected_empty_response = self._get_response_dict("projects-list-empty")

        self.client.logout()

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

    def test_projects_builds_list(self):
        url = reverse(
            "projects-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-builds-list")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_builds_list_other_user(self):
        url = reverse(
            "projects-builds-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-builds-list")
        expected_empty_response = self._get_response_dict("projects-list-empty")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_empty_response)

    def test_projects_builds_detail_anoymous_user(self):
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )
        expected_response = self._get_response_dict("projects-builds-detail")

        self.client.logout()

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_builds_detail(self):
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )
        expected_response = self._get_response_dict("projects-builds-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_builds_detail_other_user(self):
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )
        expected_response = self._get_response_dict("projects-builds-detail")
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

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

    def test_projects_builds_notifications_list_anonymous_user(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-list"
        )

        self.client.logout()

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_builds_notifications_list(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-list"
        )

        self.client.logout()

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)

        # Project and version are public.
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_builds_notifications_list_other_user(self):
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-list"
        )
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # User can see their own notifications.
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.others_project.slug,
                "parent_lookup_build__id": self.others_build.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # User can't see notifications from other users through his project.
        url = reverse(
            "projects-builds-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.others_project.slug,
                "parent_lookup_build__id": self.build.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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

    def test_projects_builds_notifitications_detail_anonymous_user(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-detail"
        )
        self.client.logout()

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_builds_notifitications_detail(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-detail"
        )

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_builds_notifitications_detail_other_user(self):
        url = reverse(
            "projects-builds-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "parent_lookup_build__id": self.build.pk,
                "notification_pk": self.notification_build.pk,
            },
        )
        expected_response = self._get_response_dict(
            "projects-builds-notifications-detail"
        )
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Project and version are public.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Project is private, version is public.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PUBLIC
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project and version are private.
        self.project.privacy_level = PRIVATE
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Project is public, but version is private.
        self.project.privacy_level = PUBLIC
        self.project.save()
        self.version.privacy_level = PRIVATE
        self.version.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.build.notifications.first().state, "read")

    def test_projects_builds_detail_has_new_fields(self):
        """Test that build detail includes commands, docs_url, commit_url, and builder fields."""
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check new fields exist
        self.assertIn("commands", data)
        self.assertIn("docs_url", data)
        self.assertIn("commit_url", data)
        self.assertIn("builder", data)

        # Validate field values
        self.assertEqual(data["builder"], "builder01")
        self.assertEqual(data["docs_url"], "http://project.readthedocs.io/en/v1.0/")
        self.assertEqual(data["commit_url"], "")
        self.assertEqual(len(data["commands"]), 1)
        self.assertEqual(data["commands"][0]["command"], "python setup.py install")

    def test_projects_builds_detail_expand_config(self):
        """Test that build detail can expand config."""
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )
        url += "?expand=config"

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check config is expanded
        self.assertIn("config", data)
        self.assertEqual(data["config"]["property"], "test value")

    def test_projects_builds_detail_expand_notifications(self):
        """Test that build detail can expand notifications."""
        url = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "build_pk": self.build.pk,
            },
        )
        url += "?expand=notifications"

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check notifications are expanded
        self.assertIn("notifications", data)
        self.assertIsInstance(data["notifications"], list)
        # We should have the notification created in the test setup
        self.assertEqual(len(data["notifications"]), 1)
