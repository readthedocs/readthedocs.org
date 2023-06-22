import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.tasks.search import (
    _create_imported_files,
    _sync_imported_files,
)

base_dir = os.path.dirname(os.path.dirname(__file__))


class ImportedFileTests(TestCase):
    fixtures = ['eric', 'test_data']

    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = self.project.versions.first()

        self.test_dir = os.path.join(base_dir, 'files')
        with override_settings(DOCROOT=self.test_dir):
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

        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.count(), 2)

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Something Else')

        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit02', 2)
        self.assertEqual(ImportedFile.objects.count(), 2)
