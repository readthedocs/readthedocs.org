# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.test import TestCase

from readthedocs.projects.models import ImportedFile, Project
from readthedocs.projects.tasks import _create_imported_files, _sync_imported_files


base_dir = os.path.dirname(os.path.dirname(__file__))


class ImportedFileTests(TestCase):
    fixtures = ['eric', 'test_data']

    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = self.project.versions.first()

        self.test_dir = os.path.join(base_dir, 'files')
        self._copy_storage_dir()
    
    def _manage_imported_files(self, version, commit, build):
        """Helper function for the tests to create and sync ImportedFiles."""
        _create_imported_files(version, commit, build)
        _sync_imported_files(version, build, set())

    def _copy_storage_dir(self):
        self.storage.copy_directory(
            self.test_dir,
            self.project.get_storage_path(
                type_='html',
                version_slug=self.version.slug,
                include_file=False,
            ),
        )

    def test_properly_created(self):
        # Only one file in the directory is HTML
        self.assertEqual(ImportedFile.objects.count(), 0)
        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.count(), 1)
        self._manage_imported_files(self.version, 'commit01', 2)
        self.assertEqual(ImportedFile.objects.count(), 1)

        self.project.cdn_enabled = True
        self.project.save()

        # CDN enabled projects => save all files
        self._manage_imported_files(self.version, 'commit01', 3)
        self.assertEqual(ImportedFile.objects.count(), 3)

    def test_update_commit(self):
        self.assertEqual(ImportedFile.objects.count(), 0)
        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.first().commit, 'commit01')
        self._manage_imported_files(self.version, 'commit02', 2)
        self.assertEqual(ImportedFile.objects.first().commit, 'commit02')

    def test_update_content(self):
        test_dir = os.path.join(base_dir, 'files')
        self.assertEqual(ImportedFile.objects.count(), 0)

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Woo')

        self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit01', 1)
        self.assertEqual(ImportedFile.objects.get(name='test.html').md5, 'c7532f22a052d716f7b2310fb52ad981')

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Something Else')

        self._copy_storage_dir()

        self._manage_imported_files(self.version, 'commit02', 2)
        self.assertNotEqual(ImportedFile.objects.get(name='test.html').md5, 'c7532f22a052d716f7b2310fb52ad981')

        self.assertEqual(ImportedFile.objects.count(), 1)
