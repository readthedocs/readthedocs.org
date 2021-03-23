import os
from unittest import mock

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.tasks import (
    _create_imported_files,
    _create_intersphinx_data,
    _sync_imported_files,
)
from readthedocs.sphinx_domains.models import SphinxDomain

base_dir = os.path.dirname(os.path.dirname(__file__))


class ImportedFileTests(TestCase):
    fixtures = ['eric', 'test_data']

    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = self.project.versions.first()

        self.test_dir = os.path.join(base_dir, 'files')
        self._copy_storage_dir()

    def _manage_imported_files(
        self,
        version,
        commit,
        build,
        search_ranking=None,
        search_ignore=None
    ):
        """Helper function for the tests to create and sync ImportedFiles."""
        search_ranking = search_ranking or {}
        search_ignore = search_ignore or []
        _create_imported_files(
            version=version,
            commit=commit,
            build=build,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )
        _sync_imported_files(version, build)

    def _copy_storage_dir(self):
        """Copy the test directory (rtd_tests/files) to storage"""
        self.storage.copy_directory(
            self.test_dir,
            self.project.get_storage_path(
                type_='html',
                version_slug=self.version.slug,
                include_file=False,
            ),
        )

    def test_properly_created(self):
        # Only 2 files in the directory is HTML (test.html, api/index.html)
        self.assertEqual(ImportedFile.objects.count(), 0)
        self._manage_imported_files(version=self.version, commit='commit01', build=1)
        self.assertEqual(ImportedFile.objects.count(), 2)
        self._manage_imported_files(version=self.version, commit='commit01', build=2)
        self.assertEqual(ImportedFile.objects.count(), 2)

        self.project.cdn_enabled = True
        self.project.save()

    def test_update_commit(self):
        self.assertEqual(ImportedFile.objects.count(), 0)
        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.first().commit, 'commit01')
        self._manage_imported_files(self.version, 'commit02', 2)
        self.assertEqual(ImportedFile.objects.first().commit, 'commit02')

    def test_page_default_rank(self):
        search_ranking = {}
        self.assertEqual(HTMLFile.objects.count(), 0)
        self._manage_imported_files(self.version, 'commit01', 1, search_ranking)

        self.assertEqual(HTMLFile.objects.count(), 2)
        self.assertEqual(HTMLFile.objects.filter(rank=0).count(), 2)

    def test_page_custom_rank_glob(self):
        search_ranking = {
            '*index.html': 5,
        }
        self._manage_imported_files(self.version, 'commit01', 1, search_ranking)

        self.assertEqual(HTMLFile.objects.count(), 2)
        file_api = HTMLFile.objects.get(path='api/index.html')
        file_test = HTMLFile.objects.get(path='test.html')
        self.assertEqual(file_api.rank, 5)
        self.assertEqual(file_test.rank, 0)

    def test_page_custom_rank_several(self):
        search_ranking = {
            'test.html': 5,
            'api/index.html': 2,
        }
        self._manage_imported_files(self.version, 'commit01', 1, search_ranking)

        self.assertEqual(HTMLFile.objects.count(), 2)
        file_api = HTMLFile.objects.get(path='api/index.html')
        file_test = HTMLFile.objects.get(path='test.html')
        self.assertEqual(file_api.rank, 2)
        self.assertEqual(file_test.rank, 5)

    def test_page_custom_rank_precedence(self):
        search_ranking = {
            '*.html': 5,
            'api/index.html': 2,
        }
        self._manage_imported_files(self.version, 'commit01', 1, search_ranking)

        self.assertEqual(HTMLFile.objects.count(), 2)
        file_api = HTMLFile.objects.get(path='api/index.html')
        file_test = HTMLFile.objects.get(path='test.html')
        self.assertEqual(file_api.rank, 2)
        self.assertEqual(file_test.rank, 5)

    def test_page_custom_rank_precedence_inverted(self):
        search_ranking = {
            'api/index.html': 2,
            '*.html': 5,
        }
        self._manage_imported_files(self.version, 'commit01', 1, search_ranking)

        self.assertEqual(HTMLFile.objects.count(), 2)
        file_api = HTMLFile.objects.get(path='api/index.html')
        file_test = HTMLFile.objects.get(path='test.html')
        self.assertEqual(file_api.rank, 5)
        self.assertEqual(file_test.rank, 5)

    def test_search_page_ignore(self):
        search_ignore = [
            'api/index.html'
        ]
        self._manage_imported_files(
            self.version,
            'commit01',
            1,
            search_ignore=search_ignore,
        )

        self.assertEqual(HTMLFile.objects.count(), 2)
        file_api = HTMLFile.objects.get(path='api/index.html')
        file_test = HTMLFile.objects.get(path='test.html')
        self.assertTrue(file_api.ignore)
        self.assertFalse(file_test.ignore)

    def test_update_content(self):
        test_dir = os.path.join(base_dir, 'files')
        self.assertEqual(ImportedFile.objects.count(), 0)

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Woo')

        self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.count(), 2)

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Something Else')

        self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit02', 2)
        self.assertEqual(ImportedFile.objects.count(), 2)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    @override_settings(RTD_INTERSPHINX_URL='https://readthedocs.org')
    @mock.patch('readthedocs.projects.tasks.os.path.exists')
    def test_create_intersphinx_data(self, mock_exists):
        mock_exists.return_Value = True

        # Test data for objects.inv file
        test_objects_inv = {
            'cpp:function': {
                'sphinx.test.function': [
                    'dummy-proj-1',
                    'dummy-version-1',
                    'test.html#epub-faq',  # file generated by ``sphinx.builders.html.StandaloneHTMLBuilder``
                    'dummy-func-name-1',
                ]
            },
            'py:function': {
                'sample.test.function': [
                    'dummy-proj-2',
                    'dummy-version-2',
                    'test.html#sample-test-func',  # file generated by ``sphinx.builders.html.StandaloneHTMLBuilder``
                    'dummy-func-name-2'
                ]
            },
            'js:function': {
                'testFunction': [
                    'dummy-proj-3',
                    'dummy-version-3',
                    'api/#test-func',  # file generated by ``sphinx.builders.dirhtml.DirectoryHTMLBuilder``
                    'dummy-func-name-3'
                ]
            }
        }

        with mock.patch(
            'sphinx.ext.intersphinx.fetch_inventory',
            return_value=test_objects_inv
        ) as mock_fetch_inventory:

            _create_imported_files(
                version=self.version,
                commit='commit01',
                build=1,
                search_ranking={},
                search_ignore=[],
            )
            _create_intersphinx_data(self.version, 'commit01', 1)

            # there will be two html files,
            # `api/index.html` and `test.html`
            self.assertEqual(
                HTMLFile.objects.all().count(),
                2
            )
            self.assertEqual(
                HTMLFile.objects.filter(path='test.html').count(),
                1
            )
            self.assertEqual(
                HTMLFile.objects.filter(path='api/index.html').count(),
                1
            )

            html_file_api = HTMLFile.objects.filter(path='api/index.html').first()

            self.assertEqual(
                SphinxDomain.objects.all().count(),
                3
            )
            self.assertEqual(
                SphinxDomain.objects.filter(html_file=html_file_api).count(),
                1
            )
            mock_fetch_inventory.assert_called_once()
            self.assertRegex(
                mock_fetch_inventory.call_args[0][2],
                r'^https://readthedocs\.org/media/.*/objects\.inv$'
            )
        self.assertEqual(ImportedFile.objects.count(), 2)

    @override_settings(RTD_INTERSPHINX_URL='http://localhost:8080')
    @mock.patch('readthedocs.projects.tasks.os.path.exists')
    def test_custom_intersphinx_url(self, mock_exists):
        mock_exists.return_Value = True

        with mock.patch(
            'sphinx.ext.intersphinx.fetch_inventory',
            return_value={}
        ) as mock_fetch_inventory:
            _create_intersphinx_data(self.version, 'commit01', 1)

            mock_fetch_inventory.assert_called_once()
            self.assertRegex(
                mock_fetch_inventory.call_args[0][2],
                '^http://localhost:8080/media/.*/objects.inv$'
            )
