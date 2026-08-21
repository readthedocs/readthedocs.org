"""
Tests for API v3 filters.

These tests verify that the django-filters on our API endpoints correctly
filter querysets. See https://github.com/readthedocs/readthedocs.org/issues/8238
"""

from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_TRIGGERED, TAG
from readthedocs.builds.models import Build
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
class BuildFilterTests(APIEndpointMixin):
    def _builds_list_url(self):
        return reverse(
            "projects-builds-list",
            kwargs={"parent_lookup_project__slug": self.project.slug},
        )

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_filter_by_commit(self):
        response = self.client.get(
            self._builds_list_url(),
            data={"commit": self.build.commit},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["commit"], self.build.commit)

    def test_filter_by_commit_miss(self):
        response = self.client.get(
            self._builds_list_url(),
            data={"commit": "nonexistent"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 0)

    def test_filter_running_true(self):
        # The default build is in "finished" state.
        # Create a running build.
        running_build = get(
            Build,
            version=self.version,
            project=self.project,
            state=BUILD_STATE_TRIGGERED,
        )
        response = self.client.get(
            self._builds_list_url(),
            data={"running": "true"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], running_build.pk)

    def test_filter_running_false(self):
        # Create a running build to make sure it's excluded.
        get(
            Build,
            version=self.version,
            project=self.project,
            state=BUILD_STATE_TRIGGERED,
        )
        response = self.client.get(
            self._builds_list_url(),
            data={"running": "false"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        # Only the finished build from setUp should be returned.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.build.pk)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
)
@mock.patch("readthedocs.projects.tasks.builds.update_docs_task", mock.MagicMock())
class VersionFilterTests(APIEndpointMixin):
    def _versions_list_url(self):
        return reverse(
            "projects-versions-list",
            kwargs={"parent_lookup_project__slug": self.project.slug},
        )

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_filter_by_slug(self):
        response = self.client.get(
            self._versions_list_url(),
            data={"slug": self.version.slug},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(
            all(self.version.slug in r["slug"] for r in results),
        )

    def test_filter_by_slug_icontains(self):
        """Slug filter uses icontains lookup."""
        response = self.client.get(
            self._versions_list_url(),
            data={"slug": self.version.slug[:3].upper()},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertIn(self.version.slug, [r["slug"] for r in results])

    def test_filter_by_slug_miss(self):
        response = self.client.get(
            self._versions_list_url(),
            data={"slug": "nonexistent-slug-xyz"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 0)

    def test_filter_by_active(self):
        response = self.client.get(
            self._versions_list_url(),
            data={"active": "true"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(all(r["active"] for r in results))

    def test_filter_by_type(self):
        response = self.client.get(
            self._versions_list_url(),
            data={"type": TAG},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(all(r["type"] == TAG for r in results))

    def test_filter_by_built(self):
        response = self.client.get(
            self._versions_list_url(),
            data={"built": "true"},
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertTrue(all(r["built"] for r in results))
