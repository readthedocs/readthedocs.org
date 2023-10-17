from contextlib import contextmanager
from unittest import mock

import pytest
from corsheaders.middleware import ACCESS_CONTROL_ALLOW_ORIGIN
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.embed.v3.views import EmbedAPIBase
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Project
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_ALLOW_ORGAZATIONS=False,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(TYPE_EMBED_API).to_item()]),
)
@mock.patch("readthedocs.embed.v3.views.build_media_storage")
class TestEmbedAPIV3Access(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(
            Project,
            slug="docs",
            privacy_level=PUBLIC,
            users=[self.user],
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.version.privacy_level = PUBLIC
        self.version.save()
        self.url = (
            reverse("embed_api_v3") + "?url=https://docs.readthedocs.io/en/latest/"
        )
        self.content = """
        <html>
            <div role=main>
                Content
            </div>
        </html>
        """

    def get(self, *args, **kwargs):
        """Wrapper around ``client.get`` to be overridden in the proxied api tests."""
        return self.client.get(*args, **kwargs)

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock

        return f

    def _mock_storage(self, storage_mock):
        storage_mock.open.side_effect = self._mock_open(self.content)

    def test_get_content_public_version_anonymous_user(self, storage_mock):
        self._mock_storage(storage_mock)
        self.client.logout()
        resp = self.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content", resp.json()["content"])
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)

    def test_get_content_private_version_anonymous_user(self, storage_mock):
        self._mock_storage(storage_mock)
        self.version.privacy_level = PRIVATE
        self.version.save()

        self.client.logout()

        resp = self.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_get_content_public_version_logged_in_user(self, storage_mock):
        self._mock_storage(storage_mock)
        self.client.force_login(self.user)

        resp = self.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content", resp.json()["content"])
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)

    def test_get_content_private_version_logged_in_user(self, storage_mock):
        self._mock_storage(storage_mock)
        self.version.privacy_level = PRIVATE
        self.version.save()

        self.client.force_login(self.user)

        resp = self.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content", resp.json()["content"])
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)

    @mock.patch.object(EmbedAPIBase, "_download_page_content")
    def test_get_content_allowed_external_page(
        self, download_page_content, storage_mock
    ):
        download_page_content.return_value = self.content

        resp = self.get(
            reverse("embed_api_v3") + "?url=https://docs.python.org/en/latest/"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Content", resp.json()["content"])
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)

    def test_get_content_not_allowed_external_page(self, storage_mock):
        resp = self.get(reverse("embed_api_v3") + "?url=https://example.com/en/latest/")
        self.assertEqual(resp.status_code, 400)


@pytest.mark.proxito
class TestProxiedEmbedAPIV3Access(TestEmbedAPIV3Access):
    def get(self, *args, **kwargs):
        return self.client.get(*args, HTTP_HOST="docs.readthedocs.io", **kwargs)

    def test_get_content_private_version_logged_in_user(self):
        """This test is skipped, since the proxied API on .org doesn't log in users."""
