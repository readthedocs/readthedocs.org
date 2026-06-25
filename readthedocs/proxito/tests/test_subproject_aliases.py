"""
End-to-end coverage for subproject aliases that contain slashes.

This file exercises every URL surface that resolves a subproject by its
alias, to make sure slash aliases (e.g. ``api/python``) work consistently:

- ``/projects/<alias>/<lang>/<version>/<file>`` doc serving
- ``/projects/<alias>/`` default-version redirect
- ``/projects/<alias>/page/<file>`` page redirect
- ``/_/downloads/<alias>/<lang>/<version>/<type>/`` proxied downloads
- ``Resolver`` building outbound URLs for a slash-aliased subproject
- Longest-prefix-match disambiguation between ``api`` and ``api/python``
"""

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
    """Hit every URL that resolves a subproject by alias with a slash alias."""

    SLASH_ALIAS = "api/python"
    HOST = "project.dev.readthedocs.io"

    def setUp(self):
        super().setUp()
        # ``BaseDocServing`` mounts ``self.subproject_alias`` at
        # ``this-is-an-alias``. Re-mount it with a slash alias.
        relation = self.project.subprojects.get(child=self.subproject_alias)
        relation.alias = self.SLASH_ALIAS
        relation.save()

    def test_docs_serving_html_file(self):
        resp = self.client.get(
            f"/projects/{self.SLASH_ALIAS}/en/latest/awesome.html",
            headers={"host": self.HOST},
        )
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-alias/latest/awesome.html",
        )

    def test_docs_serving_root_redirects_to_default_version(self):
        resp = self.client.get(
            f"/projects/{self.SLASH_ALIAS}/",
            headers={"host": self.HOST},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            f"http://{self.HOST}/projects/{self.SLASH_ALIAS}/en/latest/",
        )

    def test_page_redirect(self):
        resp = self.client.get(
            f"/projects/{self.SLASH_ALIAS}/page/awesome.html",
            headers={"host": self.HOST},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            f"http://{self.HOST}/projects/{self.SLASH_ALIAS}/en/latest/awesome.html",
        )

    def test_download_files_for_each_media_type(self):
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/{self.SLASH_ALIAS}/en/latest/{type_}/",
                headers={"host": self.HOST},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/subproject-alias/latest/subproject-alias.{extension}",
            )

    def test_resolver_builds_slash_alias_url(self):
        """``Resolver.resolve`` for the subproject embeds the slash alias path."""
        url = Resolver().resolve(self.subproject_alias)
        self.assertIn(f"/projects/{self.SLASH_ALIAS}/", url)

    def test_longest_prefix_match_wins(self):
        """When ``api`` and ``api/python`` both exist, the longer alias wins."""
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

        # /projects/api/python/... → subproject_alias (longer alias wins)
        resp = self.client.get(
            "/projects/api/python/en/latest/awesome.html",
            headers={"host": self.HOST},
        )
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-alias/latest/awesome.html",
        )

        # /projects/api/... → falls back to the shorter ``api`` alias
        resp = self.client.get(
            "/projects/api/en/latest/awesome.html",
            headers={"host": self.HOST},
        )
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/api-only/latest/awesome.html",
        )

    def test_segment_boundary_required(self):
        """A path that doesn't end on a segment boundary doesn't match."""
        # /projects/api/python-extra/... must NOT match alias ``api/python``.
        # With no matching subproject the request falls through to the
        # parent's path resolver, which returns a 404 because the path is
        # not a valid language/version pair.
        resp = self.client.get(
            "/projects/api/python-extra/en/latest/",
            headers={"host": self.HOST},
        )
        self.assertEqual(resp.status_code, 404)
