import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.embed.views import do_embed
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.models import Project

data_path = Path(__file__).parent.resolve() / 'data'


@override_settings(
    USE_SUBDOMAIN=True,
    PUBLIC_DOMAIN='readthedocs.io',
    DEBUG=True,
)
class APITest(TestCase):

    def setUp(self):
        self.project = get(
            Project,
            main_language_project=None,
            slug='project',
        )

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock
        return f

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_sphinx(self, storage_mock):
        json_file = data_path / 'sphinx/latest/index.fjson'
        html_content = data_path / 'sphinx/latest/index.html'

        json_content = json.load(json_file.open())
        json_content['body'] = html_content.open().read()

        storage_mock.exists.return_value = True
        storage_mock.open.side_effect = self._mock_open(
            json.dumps(json_content)
        )

        response = do_embed(
            project=self.project,
            version=self.project.versions.first(),
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

        self.assertDictEqual(response.data, expected)

    @mock.patch('readthedocs.embed.views.build_media_storage')
    def test_embed_mkdocs(self, storage_mock):
        json_file = data_path / 'mkdocs/latest/index.json'
        storage_mock.exists.return_value = True
        storage_mock.open.side_effect = self._mock_open(
            json_file.open().read()
        )

        self.project.versions.update(documentation_type=MKDOCS)

        response = do_embed(
            project=self.project,
            version=self.project.versions.first(),
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
        self.assertDictEqual(response.data, expected)
