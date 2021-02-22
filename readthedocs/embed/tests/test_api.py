import os
from unittest import mock

import django_dynamic_fixture as fixture
import requests_mock
from django.test import TestCase
from django.test.utils import override_settings
from readthedocsext.embed.views import do_embed

from readthedocs.projects.models import Project


MEDIA_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data'
)


@override_settings(
    USE_SUBDOMAIN=True,
    PUBLIC_DOMAIN='readthedocs.io',
    DEBUG=True,
)
class APITest(TestCase):

    def setUp(self):
        self.project = fixture.get(
            Project,
            main_language_project=None,
            slug='project',
        )

    def _mock_storage(self, storage_mock, filename):
        storage_mock.exists.return_value = True

        # when calling ``parse_mkdocs``, we already called ``parse_sphinx`` and
        # failed parsing it. The result is that the file is already opened, so
        # we need to open it again
        storage_mock.open.side_effect = [
            open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    *filename,
                )
            ),
            open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    *filename,
                )
            )
        ]

    @mock.patch('readthedocsext.embed.views.build_media_storage')
    def test_embed_sphinx(self, storage_mock):
        filename = ['data', 'json', 'sphinx', 'latest', 'index.fjson']
        self._mock_storage(storage_mock, filename)

        requests_mocker = requests_mock.Mocker()
        with requests_mocker:
            response = do_embed(
                self.project,
                self.project.versions.first(),
                'index',
                section='Features',
                path='index.html',
            )

        self.assertDictEqual(
            response.data,
            {
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
        )

    @mock.patch('readthedocsext.embed.views.build_media_storage')
    def test_embed_mkdocs(self, storage_mock):
        filename = ['data', 'json', 'mkdocs', 'latest', 'index.json']
        self._mock_storage(storage_mock, filename)

        requests_mocker = requests_mock.Mocker()
        with requests_mocker:
            response = do_embed(
                self.project,
                self.project.versions.first(),
                'index',
                section='Installation',
                path='index.html',
            )

        self.assertDictEqual(
            response.data,
            {
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
        )
