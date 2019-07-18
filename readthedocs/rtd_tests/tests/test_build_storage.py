import os
import shutil
import tempfile

from django.test import TestCase

from readthedocs.builds.storage import BuildMediaFileSystemStorage


files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')


class TestBuildMediaStorage(TestCase):
    def setUp(self):
        self.test_media_dir = tempfile.mkdtemp()
        self.storage = BuildMediaFileSystemStorage(location=self.test_media_dir)

    def tearDown(self):
        shutil.rmtree(self.test_media_dir, ignore_errors=True)

    def test_copy_directory(self):
        self.assertFalse(self.storage.exists('files/test.html'))

        self.storage.copy_directory(files_dir, 'files')
        self.assertTrue(self.storage.exists('files/test.html'))
        self.assertTrue(self.storage.exists('files/conf.py'))
        self.assertTrue(self.storage.exists('files/api.fjson'))

    def test_delete_directory(self):
        self.storage.copy_directory(files_dir, 'files')
        dirs, files = self.storage.listdir('files')
        self.assertEqual(dirs, [])
        self.assertCountEqual(files, ['api.fjson', 'conf.py', 'test.html'])

        self.storage.delete_directory('files/')
        dirs, files = self.storage.listdir('files')
        self.assertEqual(dirs, [])
        self.assertEqual(files, [])

    def test_walk(self):
        self.storage.copy_directory(files_dir, 'files')
        self.storage.copy_directory(files_dir, 'files/subfiles')

        output = list(self.storage.walk('files'))
        self.assertEqual(len(output), 2)

        top, dirs, files = output[0]
        self.assertEqual(top, 'files')
        self.assertCountEqual(dirs, ['subfiles'])
        self.assertCountEqual(files, ['api.fjson', 'conf.py', 'test.html'])

        top, dirs, files = output[1]
        self.assertEqual(top, 'files/subfiles')
        self.assertCountEqual(dirs, [])
        self.assertCountEqual(files, ['api.fjson', 'conf.py', 'test.html'])
