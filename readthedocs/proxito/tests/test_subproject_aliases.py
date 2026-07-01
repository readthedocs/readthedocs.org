"""End-to-end coverage for subproject aliases that contain slashes."""

import django_dynamic_fixture as fixture
import pytest
from django.test.utils import override_settings

from readthedocs.core.resolver import Resolver
from readthedocs.projects.constants import (
    DOWNLOADABLE_MEDIA_TYPES,
    MEDIA_TYPE_HTMLZIP,
    PUBLIC,
)
from readthedocs.projects.models import Project

from .base import BaseDocServing


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
@pytest.mark.proxito
class TestSlashSubprojectAliases(BaseDocServing):
    """Every URL that resolves a subproject by alias, exercised with ``api/python``."""

    ALIAS = "api/python"
    HOST = "project.dev.readthedocs.io"

    def setUp(self):
        super().setUp()
        # BaseDocServing mounts self.subproject_alias under "this-is-an-alias";
        # re-mount it under a slash alias for every test in this class.
        relation = self.project.subprojects.get(child=self.subproject_alias)
        relation.alias = self.ALIAS
        relation.save()

    def _get(self, path):
        return self.client.get(path, headers={"host": self.HOST})

    def test_serves_html_file(self):
        resp = self._get(f"/projects/{self.ALIAS}/en/latest/awesome.html")
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-alias/latest/awesome.html",
        )

    def test_root_redirects_to_default_version(self):
        resp = self._get(f"/projects/{self.ALIAS}/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            f"http://{self.HOST}/projects/{self.ALIAS}/en/latest/",
        )

    def test_page_redirect(self):
        resp = self._get(f"/projects/{self.ALIAS}/page/awesome.html")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            f"http://{self.HOST}/projects/{self.ALIAS}/en/latest/awesome.html",
        )

    def test_serves_downloads(self):
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self._get(f"/_/downloads/{self.ALIAS}/en/latest/{type_}/")
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/subproject-alias/latest/subproject-alias.{extension}",
            )

    def test_resolver_emits_slash_url(self):
        url = Resolver().resolve(self.subproject_alias)
        self.assertIn(f"/projects/{self.ALIAS}/", url)

    def test_longest_prefix_match_wins(self):
        # With both ``api`` and ``api/python`` mounted, the longer alias wins
        # for ``/projects/api/python/...`` and the shorter still serves
        # ``/projects/api/...``.
        nested = fixture.get(
            Project,
            slug="api-only",
            language="en",
            users=[self.eric],
            main_language_project=None,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
        )
        nested.versions.update(privacy_level=PUBLIC)
        self.project.add_subproject(nested, alias="api")

        resp = self._get("/projects/api/python/en/latest/awesome.html")
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-alias/latest/awesome.html",
        )

        resp = self._get("/projects/api/en/latest/awesome.html")
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/api-only/latest/awesome.html",
        )

    def test_segment_boundary_required(self):
        # ``api/python-extra`` must NOT match alias ``api/python`` — only full
        # path segments count. No subproject matches, so the request 404s.
        resp = self._get("/projects/api/python-extra/en/latest/")
        self.assertEqual(resp.status_code, 404)
