import os
import shutil
import tempfile
from pathlib import Path

import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.test import TestCase, override_settings

from readthedocs.builds.storage import BuildMediaFileSystemStorage

files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")


class TestBuildMediaStorage(TestCase):
    def setUp(self):
        self.test_media_dir = tempfile.mkdtemp()
        self.storage = BuildMediaFileSystemStorage(location=self.test_media_dir)

    def tearDown(self):
        shutil.rmtree(self.test_media_dir, ignore_errors=True)

    def assertFileTree(self, source, tree):
        """
        Recursively check that ``source`` from storage has the same file tree as ``tree``.

        :param source: source path in storage
        :param tree: a list of strings representing files
                     or tuples (string, list) representing directories.
        """
        dirs_tree = [e for e in tree if not isinstance(e, str)]

        dirs, files = self.storage.listdir(source)
        expected_dirs = [e[0] for e in dirs_tree]
        expected_files = [e for e in tree if isinstance(e, str)]
        self.assertCountEqual(dirs, expected_dirs)
        self.assertCountEqual(files, expected_files)

        for folder, files in dirs_tree:
            self.assertFileTree(self.storage.join(source, folder), files)

    def test_copy_directory(self):
        self.assertFalse(self.storage.exists("files/test.html"))

        with override_settings(DOCROOT=files_dir):
            self.storage.copy_directory(files_dir, "files")
        self.assertTrue(self.storage.exists("files/test.html"))
        self.assertTrue(self.storage.exists("files/conf.py"))
        self.assertTrue(self.storage.exists("files/api.fjson"))
        self.assertTrue(self.storage.exists("files/api/index.html"))
        self.assertFalse(self.storage.exists("files/test-symlink.html"))
        self.assertFalse(self.storage.exists("files/dir-symlink"))

    def test_sync_directory(self):
        tmp_files_dir = os.path.join(tempfile.mkdtemp(), "files")
        shutil.copytree(files_dir, tmp_files_dir, symlinks=True)
        storage_dir = "files"

        tree = [
            ("api", ["index.html"]),
            "404.html",
            "api.fjson",
            "conf.py",
            "index.html",
            "test.html",
        ]
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

        tree = [
            ("api", ["index.html"]),
            "404.html",
            "conf.py",
            "index.html",
            "test.html",
        ]
        os.remove(os.path.join(tmp_files_dir, "api.fjson"))
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

        tree = [
            "404.html",
            "conf.py",
            "index.html",
            "test.html",
        ]
        shutil.rmtree(os.path.join(tmp_files_dir, "api"))
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

    def test_sync_directory_source_symlink(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_symlink_dir = Path(tempfile.mkdtemp()) / "files"
        tmp_symlink_dir.symlink_to(tmp_dir)

        with override_settings(DOCROOT=tmp_dir):
            with pytest.raises(SuspiciousFileOperation, match="symbolic link"):
                self.storage.rclone_sync_directory(tmp_symlink_dir, "files")

    def test_copy_directory_source_symlink(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_symlink_dir = Path(tempfile.mkdtemp()) / "files"
        tmp_symlink_dir.symlink_to(tmp_dir)

        with override_settings(DOCROOT=tmp_dir):
            with pytest.raises(SuspiciousFileOperation, match="symbolic link"):
                self.storage.copy_directory(tmp_symlink_dir, "files")

    def test_sync_directory_source_outside_docroot(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_docroot = Path(tempfile.mkdtemp()) / "docroot"
        tmp_docroot.mkdir()

        with override_settings(DOCROOT=tmp_docroot):
            with pytest.raises(SuspiciousFileOperation, match="outside the docroot"):
                self.storage.rclone_sync_directory(tmp_dir, "files")

    def test_copy_directory_source_outside_docroot(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_docroot = Path(tempfile.mkdtemp()) / "docroot"
        tmp_docroot.mkdir()

        with override_settings(DOCROOT=tmp_docroot):
            with pytest.raises(SuspiciousFileOperation, match="outside the docroot"):
                self.storage.copy_directory(tmp_dir, "files")

    def test_delete_directory(self):
        with override_settings(DOCROOT=files_dir):
            self.storage.copy_directory(files_dir, "files")
        dirs, files = self.storage.listdir("files")
        self.assertEqual(dirs, ["api"])
        self.assertCountEqual(
            files, ["404.html", "api.fjson", "conf.py", "index.html", "test.html"]
        )

        self.storage.delete_directory("files/")
        _, files = self.storage.listdir("files")
        self.assertEqual(files, [])
        # We don't check "dirs" here - in filesystem backed storages
        # the empty directories are not deleted
        # Cloud storage generally doesn't consider empty directories to exist

        dirs, files = self.storage.listdir("files/api")
        self.assertEqual(dirs, [])
        self.assertEqual(files, [])

    def test_walk(self):
        with override_settings(DOCROOT=files_dir):
            self.storage.copy_directory(files_dir, "files")

        output = list(self.storage.walk("files"))
        self.assertEqual(len(output), 2)

        top, dirs, files = output[0]
        self.assertEqual(top, "files")
        self.assertCountEqual(dirs, ["api"])
        self.assertCountEqual(
            files, ["404.html", "api.fjson", "conf.py", "index.html", "test.html"]
        )

        top, dirs, files = output[1]
        self.assertEqual(top, "files/api")
        self.assertCountEqual(dirs, [])
        self.assertCountEqual(files, ["index.html"])

    def test_rclone_sync(self):
        tmp_files_dir = Path(tempfile.mkdtemp()) / "files"
        shutil.copytree(files_dir, tmp_files_dir, symlinks=True)
        storage_dir = "files"

        tree = [
            ("api", ["index.html"]),
            "404.html",
            "api.fjson",
            "conf.py",
            "index.html",
            "test.html",
        ]
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

        tree = [
            ("api", ["index.html"]),
            "404.html",
            "conf.py",
            "index.html",
            "test.html",
        ]
        (tmp_files_dir / "api.fjson").unlink()
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

        tree = [
            "404.html",
            "conf.py",
            "index.html",
            "test.html",
        ]
        shutil.rmtree(tmp_files_dir / "api")
        with override_settings(DOCROOT=tmp_files_dir):
            self.storage.rclone_sync_directory(tmp_files_dir, storage_dir)
        self.assertFileTree(storage_dir, tree)

    def test_rclone_sync_source_symlink(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_symlink_dir = Path(tempfile.mkdtemp()) / "files"
        tmp_symlink_dir.symlink_to(tmp_dir)

        with override_settings(DOCROOT=tmp_dir):
            with pytest.raises(SuspiciousFileOperation, match="symbolic link"):
                self.storage.rclone_sync_directory(tmp_symlink_dir, "files")

    def test_rclone_sync_source_outside_docroot(self):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_docroot = Path(tempfile.mkdtemp()) / "docroot"
        tmp_docroot.mkdir()

        with override_settings(DOCROOT=tmp_docroot):
            with pytest.raises(SuspiciousFileOperation, match="outside the docroot"):
                self.storage.rclone_sync_directory(tmp_dir, "files")
