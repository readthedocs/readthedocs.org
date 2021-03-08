import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from django_dynamic_fixture import get
from pyquery import PyQuery

from readthedocs.builds.constants import LATEST
from readthedocs.embed.views import do_embed
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.models import Project

data_path = Path(__file__).parent.resolve() / 'data'


@pytest.mark.django_db
class TestEmbedAPI:

    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        self.project = get(
            Project,
            main_language_project=None,
            slug='project',
        )
        self.version = self.project.versions.get(slug=LATEST)

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
        html_content = data_path / 'sphinx/latest/page.html'
        json_content = json.load(json_file.open())
        json_content['body'] = html_content.open().read()
        storage_mock.open.side_effect = self._mock_open(
            json.dumps(json_content)
        )

    def _get_html_content(self, html_file):
        section_content = [PyQuery(html_file.open().read()).outerHtml()]
        return section_content

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_unknown_section(self, storage_mock):
        json_file = data_path / 'sphinx/latest/index.json'
        html_file = data_path / 'sphinx/latest/index.html'

        self._patch_sphinx_json_file(
            storage_mock=storage_mock,
            json_file=json_file,
            html_file=html_file,
        )

        response = do_embed(
            project=self.project,
            version=self.version,
            doc='index',
            section='Features',
            path='index.html',
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
    def test_embed_sphinx(self, storage_mock, section):
        json_file = data_path / 'sphinx/latest/page.json'
        html_file = data_path / 'sphinx/latest/page.html'

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
                'doc': None,
                'section': section,
            },
        }

        assert response.data == expected

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_mkdocs(self, storage_mock):
        json_file = data_path / 'mkdocs/latest/index.json'
        storage_mock.exists.return_value = True
        storage_mock.open.side_effect = self._mock_open(
            json_file.open().read()
        )

        self.version.documentation_type = MKDOCS
        self.version.save()

        response = do_embed(
            project=self.project,
            version=self.version,
            doc='index',
            section='Installation',
            path='index.html',
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

        assert response.data == expected
