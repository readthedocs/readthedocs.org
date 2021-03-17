import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from django.urls import reverse
from django_dynamic_fixture import get
from pyquery import PyQuery
from rest_framework import status
from sphinx.testing.path import path

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import MKDOCS, PUBLIC
from readthedocs.projects.models import Project

data_path = Path(__file__).parent.resolve() / 'data'


class EmbedAPISetUp:

    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        self.project = get(
            Project,
            language='en',
            main_language_project=None,
            slug='project',
            privacy_level=PUBLIC,
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.version.privacy_level = PUBLIC
        self.version.save()

        settings.USE_SUBDOMAIN = True
        settings.PUBLIC_DOMAIN = 'readthedocs.io'

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
        json_content['body'] = html_content.open().read()
        storage_mock.open.side_effect = self._mock_open(
            json.dumps(json_content)
        )

    def _get_html_content(self, html_file):
        section_content = [PyQuery(html_file.open().read()).outerHtml()]
        return section_content

    def get(self, client, *args, **kwargs):
        return client.get(*args, **kwargs)


@pytest.mark.django_db
class BaseTestEmbedAPI(EmbedAPISetUp):

    def test_invalid_arguments(self, client):
        query_params = (
            {
                'project': self.project.slug,
                'version': self.version.slug,
            },
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'section': 'foo',
            },
        )

        api_endpoint = reverse('api_embed')
        for param in query_params:
            r = self.get(client, api_endpoint, param)
            assert r.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_valid_arguments(self, storage_mock, client):
        json_file = data_path / 'sphinx/latest/page.json'
        html_file = data_path / 'sphinx/latest/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        query_params = (
            # URL only
            {'url': 'https://project.readthedocs.io/en/latest/index.html#title-one'},
            {'url': 'http://project.readthedocs.io/en/latest/index.html#title-one'},
            {'url': 'http://project.readthedocs.io/en/latest/#title-one'},
            {'url': 'http://project.readthedocs.io/en/latest/index.html?foo=bar#title-one'},
            {'url': 'http://project.readthedocs.io/en/latest/?foo=bar#title-one'},

            # doc & path
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': 'title-one',
            },
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': '/index.html',
                'section': 'title-one',
            },
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'doc': 'index',
                'section': 'title-one',
            },
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'doc': 'index',
                'section': 'title-one',
            },
        )
        api_endpoint = reverse('api_embed')
        for param in query_params:
            r = self.get(client, api_endpoint, param)
            assert r.status_code == status.HTTP_200_OK

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_unknown_section(self, storage_mock, client):
        json_file = data_path / 'sphinx/latest/index.json'
        html_file = data_path / 'sphinx/latest/index.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': 'Features',
            }
        )

        expected = {
            'content': [],
            'headers': [
                {'Welcome to Read The Docs': '#'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': 'Features',
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    @pytest.mark.parametrize(
        'section',
        [
            'i-need-secrets-or-environment-variables-in-my-build',
            'title-one',
            'sub-title-one',
            'subsub-title',
        ]
    )
    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx(self, storage_mock, section, client):
        json_file = data_path / 'sphinx/latest/page.json'
        html_file = data_path / 'sphinx/latest/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': section,
            }
        )

        section_content = self._get_html_content(
            data_path / f'sphinx/latest/page-{section}.html'
        )

        expected = {
            'content': section_content,
            'headers': [
                # TODO: return the full id here
                {'I Need Secrets (or Environment Variables) in my Build': '#'},
                {'Title One': '#title-one'},
                {'Sub-title one': '#sub-title-one'},
                {'Subsub title': '#subsub-title'},
                # TODO: detect this header
                # {'Adding a new scenario to the repository': 'adding-a-new-scenario-to-the-repository'}
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': section,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    @pytest.mark.parametrize(
        'section',
        [
            'getting-started',
            'overview',
            'installation',
            'minimal-example',
            # TODO: return just one element for definition lists
            'nel87a',
            'nel87b',
        ]
    )
    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx_bibtex(self, storage_mock, section, client):
        json_file = data_path / 'sphinx/bibtex/page.json'
        html_file = data_path / 'sphinx/bibtex/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'section': section,
                'path': 'index.html',
            }
        )

        section_content = self._get_html_content(
            data_path / f'sphinx/bibtex/page-{section}.html'
        )

        expected = {
            'content': section_content,
            'headers': [
                {'Getting Started': '#'},
                {'Overview': '#overview'},
                {'Installation': '#installation'},
                {'Minimal Example': '#minimal-example'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': section,
            },
        }

        assert response.data == expected

    @pytest.mark.parametrize(
        'section',
        [
            'glossary',
            'term-builder',
            'term-configuration-directory',
            'term-directive',
            'term-document-name',
            'term-domain',
            'term-environment',
            'term-extension',
            'term-master-document',
            'term-object',
            'term-RemoveInSphinxXXXWarning',
            'term-role',
            'term-source-directory',
            'term-reStructuredText',
        ]
    )
    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx_glossary(self, storage_mock, section, client):
        # TODO: render definition lists as a definition list with one element.
        json_file = data_path / 'sphinx/glossary/page.json'
        html_file = data_path / 'sphinx/glossary/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'section': section,
                'path': 'index.html',
            }
        )

        section_content = self._get_html_content(
            data_path / f'sphinx/glossary/page-{section}.html'
        )

        expected = {
            'content': section_content,
            'headers': [
                {'Glossary': '#'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': section,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected


class TestEmbedAPI(BaseTestEmbedAPI):

    pass


@pytest.mark.proxito
class TestProxiedEmbedAPISphinx(BaseTestEmbedAPI):

    host = 'project.readthedocs.io'

    def get(self, client, *args, **kwargs):
        r = client.get(*args, HTTP_HOST=self.host, **kwargs)
        return r


@pytest.mark.sphinxtest
@pytest.mark.django_db
class TestEmbedAPISphinx(EmbedAPISetUp):

    @pytest.mark.parametrize(
        'section',
        [
            'title',
            'subtitle',
            'sub-sub-title',
            'another-title',
        ]
    )
    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx_index(self, storage_mock, section, client, make_app):
        srcdir = path(str(data_path / "sphinx/source"))
        app = make_app("html", srcdir=srcdir)
        app.build()

        json_file = Path(app.outdir).parent / 'json/index.fjson'
        storage_mock.open.side_effect = self._mock_open(
            json_file.open().read()
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': section,
            }
        )

        section_content = self._get_html_content(
            data_path / f'sphinx/source/out/index-{section}.html'
        )

        expected = {
            'content': section_content,
            'headers': [
                {'Title': '#'},
                {'Subtitle': '#subtitle'},
                {'Sub-sub title': '#sub-sub-title'},
                {'Another title': '#another-title'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': section,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    @pytest.mark.parametrize(
        'section',
        [
            'glossary',
            'term-builder',
            'term-configuration-directory',
            'term-directive',
            'term-environment',
        ]
    )
    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx_glossary(self, storage_mock, section, client, make_app):
        srcdir = path(str(data_path / "sphinx/source"))
        app = make_app("html", srcdir=srcdir)
        app.build()

        json_file = Path(app.outdir).parent / 'json/glossary.fjson'
        storage_mock.open.side_effect = self._mock_open(
            json_file.open().read()
        )

        response = self.get(
            client,
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': section,
            },
        )

        section_content = self._get_html_content(
            data_path / f'sphinx/source/out/glossary-{section}.html'
        )

        expected = {
            'content': section_content,
            'headers': [
                {'Glossary': '#'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': section,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected
