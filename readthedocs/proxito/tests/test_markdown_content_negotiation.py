"""Tests for markdown content negotiation feature."""
import pytest
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import AddonsConfig

from .base import BaseDocServing
from .mixins import MockStorageMixin


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
class TestMarkdownContentNegotiation(MockStorageMixin, BaseDocServing):
    """Test markdown content negotiation for AI agents."""

    def setUp(self):
        super().setUp()
        # Create AddonsConfig for the project
        self.addons_config = get(
            AddonsConfig,
            project=self.project,
            markdown_content_negotiation_enabled=False,  # Start disabled
        )

    def test_markdown_negotiation_disabled_by_default(self):
        """Test that content negotiation is not performed when disabled."""
        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html.md",
        ])

        url = "/en/latest/index.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should serve HTML file normally, not redirect
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

    def test_markdown_negotiation_enabled_with_accept_header(self):
        """Test that markdown is served when Accept header requests it."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html.md",
        ])

        url = "/en/latest/index.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should redirect to markdown version
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/en/latest/index.html.md")

    def test_markdown_negotiation_with_text_plain_accept(self):
        """Test that text/plain Accept header also triggers markdown negotiation."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/page.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/page.html.md",
        ])

        url = "/en/latest/page.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/plain",
            },
        )
        # Should redirect to markdown version
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/en/latest/page.html.md")

    def test_markdown_negotiation_no_markdown_file(self):
        """Test that HTML is served when markdown version doesn't exist."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/page.html",
        ])

        url = "/en/latest/page.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should serve HTML normally
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/page.html",
        )

    def test_markdown_negotiation_without_accept_header(self):
        """Test that HTML is served when Accept header doesn't request markdown."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html.md",
        ])

        url = "/en/latest/index.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/html",
            },
        )
        # Should serve HTML normally
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

    def test_markdown_negotiation_with_alternative_pattern(self):
        """Test markdown negotiation with .md extension instead of .html.md."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/page.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/page.md",
        ])

        url = "/en/latest/page.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should redirect to markdown version
        self.assertEqual(resp.status_code, 302)
        # Since only page.md exists (not page.html.md), it should redirect to page.md
        self.assertEqual(resp["Location"], "/en/latest/page.md")

    def test_markdown_negotiation_with_subdirectory(self):
        """Test markdown negotiation for files in subdirectories."""
        # Enable markdown negotiation
        self.addons_config.markdown_content_negotiation_enabled = True
        self.addons_config.save()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/subdir/page.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/subdir/page.html.md",
        ])

        url = "/en/latest/subdir/page.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should redirect to markdown version
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/en/latest/subdir/page.html.md")

    def test_markdown_negotiation_project_without_addons_config(self):
        """Test that content negotiation handles projects without AddonsConfig."""
        # Delete the addons config
        self.addons_config.delete()

        self._storage_exists([
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html",
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
            ) + "/index.html.md",
        ])

        url = "/en/latest/index.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(
            url,
            headers={
                "host": host,
                "Accept": "text/markdown",
            },
        )
        # Should serve HTML normally (feature not enabled)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )
