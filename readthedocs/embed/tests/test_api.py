import json
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from django.urls import reverse
from django_dynamic_fixture import get
from pyquery import PyQuery
from rest_framework import status

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import MKDOCS, PUBLIC
from readthedocs.projects.models import Project
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import RTDProductFeature

data_path = Path(__file__).parent.resolve() / "data"


@pytest.mark.django_db
class BaseTestEmbedAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        self.project = get(
            Project,
            language="en",
            main_language_project=None,
            slug="project",
            privacy_level=PUBLIC,
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.version.privacy_level = PUBLIC
        self.version.save()

        settings.PUBLIC_DOMAIN = "readthedocs.io"
        settings.RTD_DEFAULT_FEATURES = dict(
            [RTDProductFeature(TYPE_EMBED_API).to_item()]
        )

    def get(self, client, *args, **kwargs):
        """Wrapper around ``client.get`` to be overridden in the proxied api tests."""
        return client.get(*args, **kwargs)

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock

        return f

    def _patch_sphinx_json_file(self, storage_mock, json_file, html_file):
        storage_mock.exists.return_value = True
        html_content = data_path / html_file
        json_content = json.load(json_file.open())
        json_content["body"] = html_content.open().read()
        storage_mock.open.side_effect = self._mock_open(json.dumps(json_content))

    def _get_html_content(self, html_file):
        section_content = [PyQuery(html_file.open().read()).outerHtml()]
        return section_content

    def test_invalid_arguments(self, client):
        query_params = (
            {
                "project": self.project.slug,
                "version": self.version.slug,
            },
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "section": "foo",
            },
        )

        api_endpoint = reverse("embed_api")
        for param in query_params:
            r = self.get(client, api_endpoint, param)
            assert r.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch("readthedocs.embed.views.build_media_storage")
    def test_valid_arguments(self, storage_mock, client):
        json_file = data_path / "sphinx/latest/page.json"
        html_file = data_path / "sphinx/latest/page.html"

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        query_params = (
            # URL only
            {"url": "https://project.readthedocs.io/en/latest/index.html#title-one"},
            {"url": "http://project.readthedocs.io/en/latest/index.html#title-one"},
            {"url": "http://project.readthedocs.io/en/latest/#title-one"},
            {
                "url": "http://project.readthedocs.io/en/latest/index.html?foo=bar#title-one"
            },
            {"url": "http://project.readthedocs.io/en/latest/?foo=bar#title-one"},
            # doc & path
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "section": "title-one",
            },
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "/index.html",
                "section": "title-one",
            },
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "doc": "index",
                "section": "title-one",
            },
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "doc": "index",
                "section": "title-one",
            },
        )
        api_endpoint = reverse("embed_api")
        for param in query_params:
            r = self.get(client, api_endpoint, param)
            assert r.status_code == status.HTTP_200_OK

    def test_no_access(self, client, settings):
        settings.RTD_DEFAULT_FEATURES = {}
        api_endpoint = reverse("embed_api")
        r = self.get(
            client,
            api_endpoint,
            {"url": "https://project.readthedocs.io/en/latest/index.html#title-one"},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    @mock.patch("readthedocs.embed.views.build_media_storage")
    def test_embed_unknown_section(self, storage_mock, client):
        json_file = data_path / "sphinx/latest/index.json"
        html_file = data_path / "sphinx/latest/index.html"

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse("embed_api"),
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "section": "Features",
            },
        )

        expected = {
            "content": [],
            "headers": [
                {"Welcome to Read the Docs": "#"},
            ],
            "url": "http://project.readthedocs.io/en/latest/index.html",
            "meta": {
                "project": "project",
                "version": "latest",
                "doc": "index",
                "section": "Features",
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    @pytest.mark.parametrize(
        "path, docname",
        [
            ("index.html", "index"),
            ("index/", "index"),
            ("index//", "index"),
            ("/index.html", "index"),
            ("/index/", "index"),
            ("/index//", "index"),
            ("guides/users/index.html", "guides/users/index"),
            ("guides/users/", "guides/users"),
            ("/guides/users/", "guides/users"),
        ],
    )
    @mock.patch("readthedocs.embed.views.build_media_storage")
    def test_embed_dir_path(self, storage_mock, path, docname, client):
        json_file = data_path / "sphinx/latest/page.json"
        html_file = data_path / "sphinx/latest/page.html"

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse("embed_api"),
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": path,
                "section": "title-one",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["meta"]["doc"] == docname

    @pytest.mark.parametrize(
        "section",
        [
            "i-need-secrets-or-environment-variables-in-my-build",
            "title-one",
            "sub-title-one",
            "subsub-title",
        ],
    )
    @mock.patch("readthedocs.embed.views.build_media_storage")
    def test_embed_sphinx(self, storage_mock, section, client):
        json_file = data_path / "sphinx/latest/page.json"
        html_file = data_path / "sphinx/latest/page.html"

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse("embed_api"),
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "section": section,
            },
        )

        section_content = self._get_html_content(
            data_path / f"sphinx/latest/page-{section}.html"
        )

        expected = {
            "content": section_content,
            "headers": [
                # TODO: return the full id here
                {"I Need Secrets (or Environment Variables) in my Build": "#"},
                {"Title One": "#title-one"},
                {"Sub-title one": "#sub-title-one"},
                {"Subsub title": "#subsub-title"},
                # TODO: detect this header
                # {'Adding a new scenario to the repository': 'adding-a-new-scenario-to-the-repository'}
            ],
            "url": "http://project.readthedocs.io/en/latest/index.html",
            "meta": {
                "project": "project",
                "version": "latest",
                "doc": "index",
                "section": section,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected
        assert response["Cache-tag"] == "project,project:latest"

    def test_embed_mkdocs(self, client):
        """API v2 doesn't support mkdocs."""
        self.version.documentation_type = MKDOCS
        self.version.save()

        response = self.get(
            client,
            reverse("embed_api"),
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "section": "Installation",
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_no_access(self, client, settings):
        settings.RTD_DEFAULT_FEATURES = {}
        response = self.get(
            client,
            reverse("embed_api"),
            {
                "project": self.project.slug,
                "version": self.version.slug,
                "path": "index.html",
                "section": "title-one",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEmbedAPI(BaseTestEmbedAPI):
    pass


@pytest.mark.proxito
class TestProxiedEmbedAPI(BaseTestEmbedAPI):
    host = "project.readthedocs.io"

    def get(self, client, *args, **kwargs):
        r = client.get(*args, HTTP_HOST=self.host, **kwargs)
        return r
