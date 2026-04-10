import json
from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff import get_base_snapshot, get_diff, snapshot_base_html, write_base_snapshot
from readthedocs.filetreediff.dataclasses import BaseSnapshot
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest


# We are overriding the storage class instead of using RTD_BUILD_MEDIA_STORAGE,
# since the setting is evaluated just once (first test to use the storage
# backend will set it for the whole test suite).
@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsFileTreeDiff(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version_a = self.project.versions.get(slug=LATEST)
        self.build_a_old = get(
            Build,
            project=self.project,
            version=self.version_a,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.build_a = get(
            Build,
            project=self.project,
            version=self.version_a,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.version_b = get(
            Version,
            project=self.project,
            slug="v2",
            active=True,
            built=True,
        )
        self.build_b_old = get(
            Build,
            project=self.project,
            version=self.version_b,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.build_b = get(
            Build,
            project=self.project,
            version=self.version_b,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock

        return f

    def _mock_manifest(self, build_id: int, files: dict[str, str]):
        return self._mock_open(
            json.dumps(
                {
                    "build": {"id": build_id},
                    "files": {
                        file_path: {"main_content_hash": main_content_hash}
                        for file_path, main_content_hash in files.items()
                    },
                }
            )
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_no_changes(self, storage_open):
        files_a = {
            "index.html": "hash1",
            "tutorials/index.html": "hash2",
        }
        storage_open.side_effect = [
            self._mock_manifest(self.build_a.id, files_a)(),
            self._mock_manifest(self.build_b.id, files_a)(),
        ]
        diff = get_diff(self.version_a, self.version_b)
        assert diff.added == []
        assert diff.deleted == []
        assert diff.modified == []
        assert not diff.outdated

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_changes(self, storage_open):
        files_a = {
            "index.html": "hash1",
            "tutorials/index.html": "hash2",
            "new-file.html": "hash-new",
        }
        files_b = {
            "index.html": "hash1",
            "tutorials/index.html": "hash-changed",
            "deleted.html": "hash-deleted",
        }
        storage_open.side_effect = [
            self._mock_manifest(self.build_a.id, files_a)(),
            self._mock_manifest(self.build_b.id, files_b)(),
        ]
        diff = get_diff(self.version_a, self.version_b)
        assert [file.path for file in diff.files] == ["deleted.html", "new-file.html", "tutorials/index.html"]
        assert [file.path for file in diff.added] == ["new-file.html"]
        assert [file.path for file in diff.deleted] == ["deleted.html"]
        assert [file.path for file in diff.modified] == ["tutorials/index.html"]
        assert not diff.outdated

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_missing_manifest(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        diff = get_diff(self.version_a, self.version_b)
        assert diff is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_outdated_diff(self, storage_open):
        files_a = {
            "index.html": "hash1",
            "tutorials/index.html": "hash2",
            "new-file.html": "hash-new",
        }
        files_b = {
            "index.html": "hash1",
            "tutorials/index.html": "hash-changed",
            "deleted.html": "hash-deleted",
        }
        storage_open.side_effect = [
            self._mock_manifest(self.build_a_old.id, files_a)(),
            self._mock_manifest(self.build_b_old.id, files_b)(),
        ]
        diff = get_diff(self.version_a, self.version_b)
        assert [file.path for file in diff.files] == ["deleted.html", "new-file.html", "tutorials/index.html"]
        assert [file.path for file in diff.added] == ["new-file.html"]
        assert [file.path for file in diff.deleted] == ["deleted.html"]
        assert [file.path for file in diff.modified] == ["tutorials/index.html"]
        assert diff.outdated


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestBaseSnapshot(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.base_version = self.project.versions.get(slug=LATEST)
        self.base_build = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.pr_version = get(
            Version,
            project=self.project,
            slug="123",
            active=True,
            built=True,
            type=EXTERNAL,
        )

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock

        return f

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_get_base_snapshot(self, storage_open):
        snapshot_data = json.dumps(
            {"base_build_id": self.base_build.id, "base_version_slug": "latest"}
        )
        storage_open.return_value = self._mock_open(snapshot_data)()
        snapshot = get_base_snapshot(self.pr_version)
        assert snapshot is not None
        assert snapshot.base_build_id == self.base_build.id
        assert snapshot.base_version_slug == "latest"

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_get_base_snapshot_not_found(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        snapshot = get_base_snapshot(self.pr_version)
        assert snapshot is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_write_base_snapshot(self, storage_open):
        mock_file = mock.MagicMock()
        storage_open.return_value.__enter__ = mock.MagicMock(return_value=mock_file)
        storage_open.return_value.__exit__ = mock.MagicMock(return_value=False)

        snapshot = BaseSnapshot(
            base_build_id=self.base_build.id,
            base_version_slug="latest",
        )
        write_base_snapshot(self.pr_version, snapshot)
        storage_open.assert_called_once()
        mock_file.write.assert_called()

    @mock.patch("readthedocs.filetreediff.write_base_snapshot")
    @mock.patch("readthedocs.filetreediff.get_base_snapshot")
    @mock.patch("readthedocs.filetreediff.build_media_storage")
    def test_snapshot_base_html(self, mock_storage, mock_get_snapshot, mock_write_snapshot):
        # No existing snapshot.
        mock_get_snapshot.return_value = None
        snapshot_base_html(self.pr_version, self.base_version)
        mock_storage.rclone_copy_remote_directory.assert_called_once()
        call_kwargs = mock_storage.rclone_copy_remote_directory.call_args
        assert call_kwargs.kwargs.get("include") == "*.html"
        mock_write_snapshot.assert_called_once()

    @mock.patch("readthedocs.filetreediff.write_base_snapshot")
    @mock.patch("readthedocs.filetreediff.get_base_snapshot")
    @mock.patch("readthedocs.filetreediff.build_media_storage")
    def test_snapshot_base_html_skips_if_exists(self, mock_storage, mock_get_snapshot, mock_write_snapshot):
        """If a base snapshot already exists, don't re-copy."""
        mock_get_snapshot.return_value = BaseSnapshot(
            base_build_id=self.base_build.id,
            base_version_slug="latest",
        )
        snapshot_base_html(self.pr_version, self.base_version)
        mock_storage.rclone_copy_remote_directory.assert_not_called()
        mock_write_snapshot.assert_not_called()

    def test_snapshot_base_html_no_successful_build(self):
        """If base version has no successful build, skip snapshot."""
        Build.objects.filter(version=self.base_version).delete()
        # Should not raise, just skip.
        with mock.patch("readthedocs.filetreediff.build_media_storage"):
            snapshot_base_html(self.pr_version, self.base_version)
