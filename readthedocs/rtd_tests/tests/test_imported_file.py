from __future__ import absolute_import
import os
from django.test import TestCase

from readthedocs.projects.tasks import _manage_imported_files
from readthedocs.projects.models import Project, ImportedFile

base_dir = os.path.dirname(os.path.dirname(__file__))


class ImportedFileTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = self.project.versions.first()

    def test_properly_created(self):
        test_dir = os.path.join(base_dir, 'files')
        self.assertEqual(ImportedFile.objects.count(), 0)
        _manage_imported_files(self.version, test_dir, 'commit01')
        self.assertEqual(ImportedFile.objects.count(), 2)
        _manage_imported_files(self.version, test_dir, 'commit01')
        self.assertEqual(ImportedFile.objects.count(), 2)

    def test_update_commit(self):
        test_dir = os.path.join(base_dir, 'files')
        self.assertEqual(ImportedFile.objects.count(), 0)
        _manage_imported_files(self.version, test_dir, 'commit01')
        self.assertEqual(ImportedFile.objects.first().commit, 'commit01')
        _manage_imported_files(self.version, test_dir, 'commit02')
        self.assertEqual(ImportedFile.objects.first().commit, 'commit02')

    def test_update_content(self):
        test_dir = os.path.join(base_dir, 'files')
        self.assertEqual(ImportedFile.objects.count(), 0)

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Woo')

        _manage_imported_files(self.version, test_dir, 'commit01')
        self.assertEqual(ImportedFile.objects.get(name='test.html').md5, 'c7532f22a052d716f7b2310fb52ad981')

        with open(os.path.join(test_dir, 'test.html'), 'w+') as f:
            f.write('Something Else')

        _manage_imported_files(self.version, test_dir, 'commit02')
        self.assertNotEqual(ImportedFile.objects.get(name='test.html').md5, 'c7532f22a052d716f7b2310fb52ad981')

        self.assertEqual(ImportedFile.objects.count(), 2)
