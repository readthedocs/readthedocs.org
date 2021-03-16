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

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import MKDOCS, PUBLIC
from readthedocs.projects.models import Project

data_path = Path(__file__).parent.resolve() / 'data'


@pytest.mark.django_db
class TestEmbedAPI:

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
            r = client.get(api_endpoint, param)
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
            r = client.get(api_endpoint, param)
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

        response = client.get(
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

        response = client.get(
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
    def test_embed_sphinx_bibtex(self, storage_mock, section):
        json_file = data_path / 'sphinx/bibtex/page.json'
        html_file = data_path / 'sphinx/bibtex/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = do_embed(
            project=self.project,
            version=self.version,
            section=section,
            path='index.html',
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
                'doc': None,
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
    def test_embed_sphinx_glossary(self, storage_mock, section):
        # TODO: render definition lists as a definition list with one element.
        json_file = data_path / 'sphinx/glossary/page.json'
        html_file = data_path / 'sphinx/glossary/page.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = do_embed(
            project=self.project,
            version=self.version,
            section=section,
            path='index.html',
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
                'doc': None,
                'section': section,
            },
        }

        assert response.data == expected

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_mkdocs(self, storage_mock, client):
        json_file = data_path / 'mkdocs/latest/index.json'
        storage_mock.exists.return_value = True
        storage_mock.open.side_effect = self._mock_open(
            json_file.open().read()
        )

        self.version.documentation_type = MKDOCS
        self.version.save()

        response = client.get(
            reverse('api_embed'),
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'path': 'index.html',
                'section': 'Installation',
            }
        )

        expected = {
            'content': mock.ANY,  # too long to compare here
            'headers': [
                {'Overview': 'overview'},
                {'Installation': 'installation'},
                {'Getting Started': 'getting-started'},
                {'Adding pages': 'adding-pages'},
                {'Theming our documentation': 'theming-our-documentation'},
                {'Changing the Favicon Icon': 'changing-the-favicon-icon'},
                {'Building the site': 'building-the-site'},
                {'Other Commands and Options': 'other-commands-and-options'},
                {'Deploying': 'deploying'},
                {'Getting help': 'getting-help'},
            ],
            'url': 'http://project.readthedocs.io/en/latest/index.html',
            'meta': {
                'project': 'project',
                'version': 'latest',
                'doc': 'index',
                'section': 'Installation',
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected
