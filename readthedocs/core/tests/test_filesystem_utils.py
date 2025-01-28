from pathlib import Path
from tempfile import mkdtemp

import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.test import TestCase, override_settings

from readthedocs.core.utils.filesystem import safe_copytree, safe_open, safe_rmtree
from readthedocs.doc_builder.exceptions import (
    BuildUserError,
    SymlinkOutsideBasePath,
    UnsupportedSymlinkFileError,
)


class TestFileSystemUtils(TestCase):
    def assert_files_equal(self, directory, files):
        self.assertEqual(
            {str(p.relative_to(directory)) for p in directory.iterdir()}, files
        )

    def test_copytree(self):
        from_directory = Path(mkdtemp())
        docroot_path = from_directory.parent
        to_directory = Path(mkdtemp()) / "target"

        (from_directory / "test.txt").touch()

        self.assertFalse(to_directory.exists())

        with override_settings(DOCROOT=docroot_path):
            safe_copytree(from_directory, to_directory)

        self.assert_files_equal(to_directory, {"test.txt"})

    def test_copytree_outside_docroot(self):
        from_directory = Path(mkdtemp())
        (from_directory / "test.txt").touch()
        to_directory = Path(mkdtemp()) / "target"
        docroot_path = Path(mkdtemp())

        with pytest.raises(SuspiciousFileOperation):
            with override_settings(DOCROOT=docroot_path):
                safe_copytree(from_directory, to_directory)

    def test_copytree_with_symlinks(self):
        from_directory = Path(mkdtemp())
        docroot_path = from_directory.parent
        to_directory = Path(mkdtemp()) / "target"

        file_a = from_directory / "test.txt"
        file_a.touch()

        symlink_a = from_directory / "symlink.txt"
        symlink_a.symlink_to(file_a)
        symlink_b = from_directory / "symlink-dir"
        symlink_b.symlink_to(to_directory.parent)

        self.assertFalse(to_directory.exists())

        with override_settings(DOCROOT=docroot_path):
            safe_copytree(from_directory, to_directory)

        # Symlinks are copied as symlinks, not as files.
        self.assert_files_equal(
            to_directory, {"test.txt", "symlink.txt", "symlink-dir"}
        )
        self.assertTrue((to_directory / "symlink.txt").is_symlink())
        self.assertTrue((to_directory / "symlink-dir").is_symlink())

    def test_copytree_from_dir_as_symlink(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        from_directory = root_directory / "a"
        from_directory.mkdir()
        (from_directory / "test.txt").touch()

        to_directory = root_directory / "b"

        from_directory_symlink = root_directory / "symlink-a"
        from_directory_symlink.symlink_to(from_directory)

        self.assertFalse(to_directory.exists())

        with override_settings(DOCROOT=docroot_path):
            self.assertFalse(safe_copytree(from_directory_symlink, to_directory))

        self.assertFalse(to_directory.exists())

    def test_open(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        file_a = root_directory / "test.txt"
        file_a.touch()

        with override_settings(DOCROOT=docroot_path):
            context_manager = safe_open(file_a, allow_symlinks=False)
            self.assertIsNotNone(context_manager)

        with override_settings(DOCROOT=docroot_path):
            context_manager = safe_open(
                file_a, allow_symlinks=True, base_path=root_directory
            )
            self.assertIsNotNone(context_manager)

    def test_open_large_file(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        file_a = root_directory / "test.txt"
        file_a.write_bytes(b"0" * (1024 * 2))

        with override_settings(DOCROOT=docroot_path):
            with pytest.raises(BuildUserError):
                safe_open(file_a, max_size_bytes=1024)

    def test_write_file(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        file_a = root_directory / "test.txt"

        with override_settings(DOCROOT=docroot_path):
            with safe_open(file_a, mode="w") as f:
                f.write("Hello World")
            self.assertEqual(file_a.read_text(), "Hello World")

    def test_open_outside_docroot(self):
        root_directory = Path(mkdtemp())
        docroot_path = Path(mkdtemp())
        file_a = root_directory / "test.txt"
        file_a.touch()

        with pytest.raises(SuspiciousFileOperation):
            with override_settings(DOCROOT=docroot_path):
                safe_open(file_a)

    def test_open_with_symlinks(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        file_a = root_directory / "test.txt"
        file_a.touch()

        symlink_a = root_directory / "symlink.txt"
        symlink_a.symlink_to(file_a)

        # Symlinks aren't allowed.
        with pytest.raises(UnsupportedSymlinkFileError):
            with override_settings(DOCROOT=docroot_path):
                safe_open(symlink_a, allow_symlinks=False)

        # Symlinks are allowed if they are under the root_directory.
        with override_settings(DOCROOT=docroot_path):
            context_manager = safe_open(
                symlink_a, allow_symlinks=True, base_path=root_directory
            )
            self.assertIsNotNone(context_manager)

        # Symlinks aren't allowed if they aren't under the root_directory.
        with pytest.raises(SymlinkOutsideBasePath):
            with override_settings(DOCROOT=docroot_path):
                new_root_directory = root_directory / "dir"
                new_root_directory.mkdir()
                safe_open(symlink_a, allow_symlinks=True, base_path=new_root_directory)

    def test_rmtree(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory
        (root_directory / "test.txt").touch()

        self.assertTrue(root_directory.exists())

        with override_settings(DOCROOT=docroot_path):
            safe_rmtree(root_directory)
            self.assertFalse(root_directory.exists())

    def test_rmtree_outside_docroot(self):
        root_directory = Path(mkdtemp())
        docroot_path = Path(mkdtemp())
        (root_directory / "test.txt").touch()

        self.assertTrue(root_directory.exists())

        with pytest.raises(SuspiciousFileOperation):
            with override_settings(DOCROOT=docroot_path):
                safe_rmtree(root_directory)

    def test_rmtree_with_symlinks(self):
        root_directory = Path(mkdtemp())
        docroot_path = root_directory

        dir_a = root_directory / "test"
        dir_a.mkdir()
        (dir_a / "test.txt").touch()

        symlink_a = root_directory / "symlink"
        symlink_a.symlink_to(dir_a)

        # Directories that point to a symlink aren't deleted.
        self.assertTrue(symlink_a.exists())
        with override_settings(DOCROOT=docroot_path):
            safe_rmtree(symlink_a)
            self.assertTrue(symlink_a.exists())
