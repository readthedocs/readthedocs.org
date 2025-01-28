from unittest import mock

import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import HTMLFile, Project

from .mixins import APIEndpointMixin


@override_settings(ALLOW_PRIVATE_REPOS=False)
class VersionsEndpointTests(APIEndpointMixin):
    def test_projects_versions_list_anonymous_user(self):
        url = reverse(
            "projects-versions-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        # Versions are public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["results"]), 2)
        self.assertEqual(json_data["results"][0]["slug"], "v1.0")
        self.assertEqual(json_data["results"][1]["slug"], "latest")

        # Versions are private
        self.project.versions.update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["results"]), 0)

    def test_projects_versions_list(self):
        url = reverse(
            "projects-versions-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Versions are public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["slug"], "v1.0")
        self.assertEqual(response["results"][1]["slug"], "latest")

        # Versions are private
        Project.objects.filter(slug=self.project.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        response = response.json()
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["slug"], "v1.0")
        self.assertEqual(response["results"][1]["slug"], "latest")

    def test_projects_versions_list_other_user(self):
        url = reverse(
            "projects-versions-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Versions are public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["results"]), 2)
        self.assertEqual(json_data["results"][0]["slug"], "v1.0")
        self.assertEqual(json_data["results"][1]["slug"], "latest")

        # Versions are private
        self.project.versions.update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(len(json_data["results"]), 0)

    def test_projects_versions_detail_anonymous_user(self):
        url = reverse(
            "projects-versions-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "version_slug": "v1.0",
            },
        )
        expected_response = self._get_response_dict("projects-versions-detail")

        self.client.logout()

        # Version is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Version is private
        self.project.versions.update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_versions_detail(self):
        url = reverse(
            "projects-versions-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "version_slug": "v1.0",
            },
        )
        expected_response = self._get_response_dict("projects-versions-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Version is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Version is private
        self.project.versions.update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected_response["privacy_level"] = "private"
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_versions_detail_other_user(self):
        url = reverse(
            "projects-versions-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "version_slug": "v1.0",
            },
        )
        expected_response = self._get_response_dict("projects-versions-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Version is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Version is private
        self.project.versions.update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_detail_privacy_levels_allowed(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-versions-detail"),
        )

        self.version.privacy_level = "private"
        self.version.save()
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        expected = self._get_response_dict("projects-versions-detail")
        expected["privacy_level"] = "private"
        self.assertDictEqual(
            response.json(),
            expected,
        )

    def test_nonexistent_project_version_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": "nonexistent",
                    "version_slug": "latest",
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_projects_versions_detail_unique(self):
        second_project = fixture.get(
            Project,
            name="second project",
            slug="second-project",
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        second_version = fixture.get(
            Version,
            slug=self.version.slug,
            verbose_name=self.version.verbose_name,
            identifier="a1b2c3",
            project=second_project,
            active=True,
            built=True,
            type=TAG,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch(
        "readthedocs.projects.tasks.utils.clean_project_resources", new=mock.MagicMock
    )
    def test_projects_versions_partial_update(self):
        self.assertTrue(self.version.active)
        self.assertFalse(self.version.hidden)
        url = reverse(
            "projects-versions-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "version_slug": self.version.slug,
            },
        )
        data = {
            "active": False,
            "hidden": True,
        }

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)

        self.version.refresh_from_db()
        self.assertEqual(self.version.verbose_name, "v1.0")
        self.assertEqual(self.version.slug, "v1.0")
        self.assertEqual(self.version.identifier, "a1b2c3")
        self.assertFalse(self.version.active)
        self.assertTrue(self.version.hidden)
        self.assertFalse(self.version.built)
        self.assertEqual(self.version.type, TAG)

    def test_projects_versions_partial_update_privacy_levels_disabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertEqual(self.version.privacy_level, "public")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_partial_update_privacy_levels_enabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertEqual(self.version.privacy_level, "private")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_partial_update_invalid_privacy_levels(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "publicprivate",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.version.privacy_level, "public")

    @mock.patch("readthedocs.builds.models.trigger_build")
    @mock.patch("readthedocs.projects.tasks.utils.clean_project_resources")
    def test_activate_version(self, clean_project_resources, trigger_build):
        self.version.active = False
        self.version.save()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertFalse(self.version.active)
        data = {"active": True}
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertTrue(self.version.active)
        clean_project_resources.assert_not_called()
        trigger_build.assert_called_once()

    @mock.patch("readthedocs.builds.models.trigger_build")
    @mock.patch("readthedocs.projects.tasks.search.remove_search_indexes")
    @mock.patch("readthedocs.projects.tasks.utils.remove_build_storage_paths")
    def test_deactivate_version(
        self, remove_build_storage_paths, remove_search_indexes, trigger_build
    ):
        another_version = get(Version, project=self.project, active=True)
        get(
            HTMLFile,
            project=self.project,
            version=another_version,
            name="index.html",
            path="index.html",
        )
        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            name="index.html",
            path="index.html",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {"active": False}
        self.assertTrue(self.version.active)
        self.assertTrue(self.version.built)
        self.assertTrue(another_version.imported_files.exists())
        self.assertTrue(self.version.imported_files.exists())
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertFalse(self.version.active)
        self.assertFalse(self.version.built)
        self.assertFalse(self.version.imported_files.exists())
        self.assertTrue(another_version.imported_files.exists())
        remove_build_storage_paths.delay.assert_called_once()
        remove_search_indexes.delay.assert_called_once()
        trigger_build.assert_not_called()

    def test_projects_version_external(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.version.type = EXTERNAL
        self.version.save()

        response = self.client.get(
            reverse(
                "projects-versions-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["slug"], "latest")

        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data={
                "active": False,
            },
        )
        self.assertEqual(response.status_code, 404)
