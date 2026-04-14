import json
from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff import get_diff, snapshot_base_manifest
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest


def _mock_open(content):
    @contextmanager
    def f(*args, **kwargs):
        read_mock = mock.MagicMock()
        read_mock.read.return_value = content
        yield read_mock

    return f


def _mock_manifest(build_id: int, files: dict[str, str], merge_base: str | None = None):
    return _mock_open(
        json.dumps(
            {
                "build": {"id": build_id},
                "merge_base": merge_base,
                "files": {
                    path: {"main_content_hash": content_hash}
                    for path, content_hash in files.items()
                },
            }
        )
    )


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

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_no_changes(self, storage_open):
        files_a = {
            "index.html": "hash1",
            "tutorials/index.html": "hash2",
        }
        storage_open.side_effect = [
            _mock_manifest(self.build_a.id, files_a)(),
            _mock_manifest(self.build_b.id, files_a)(),
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
            _mock_manifest(self.build_a.id, files_a)(),
            _mock_manifest(self.build_b.id, files_b)(),
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
            _mock_manifest(self.build_a_old.id, files_a)(),
            _mock_manifest(self.build_b_old.id, files_b)(),
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
class TestsBaseManifestSnapshot(TestCase):
    """Tests for base manifest snapshotting (stale branch fix)."""

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
            slug="pr-42",
            verbose_name="42",
            type=EXTERNAL,
            active=True,
            built=True,
        )
        self.pr_build = get(
            Build,
            project=self.project,
            version=self.pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_used_over_live_base(self, storage_open):
        """For PRs, get_diff uses the snapshot instead of the live base manifest."""
        pr_files = {"index.html": "pr-hash", "new-page.html": "new-hash"}
        snapshot_files = {"index.html": "original-hash"}

        # get_diff reads: 1) PR manifest, 2) base snapshot
        storage_open.side_effect = [
            _mock_manifest(self.pr_build.id, pr_files)(),
            _mock_manifest(self.base_build.id, snapshot_files)(),
        ]
        diff = get_diff(self.pr_version, self.base_version)
        assert [f.path for f in diff.added] == ["new-page.html"]
        assert [f.path for f in diff.modified] == ["index.html"]
        assert diff.deleted == []

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_fallback_to_live_base_when_no_snapshot(self, storage_open):
        pr_files = {"index.html": "pr-hash"}
        live_base_files = {"index.html": "live-hash"}

        # 1) PR manifest, 2) snapshot miss, 3) live base manifest
        storage_open.side_effect = [
            _mock_manifest(self.pr_build.id, pr_files)(),
            FileNotFoundError,
            _mock_manifest(self.base_build.id, live_base_files)(),
        ]
        diff = get_diff(self.pr_version, self.base_version)
        assert [f.path for f in diff.modified] == ["index.html"]

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_prevents_false_positives_from_stale_base(self, storage_open):
        """
        PR only changed index.html. Meanwhile base added extra.html.
        Without snapshot the diff would show extra.html as deleted — bogus.
        """
        pr_files = {"index.html": "pr-hash", "about.html": "same-hash"}
        snapshot_files = {"index.html": "original-hash", "about.html": "same-hash"}

        storage_open.side_effect = [
            _mock_manifest(self.pr_build.id, pr_files)(),
            _mock_manifest(self.base_build.id, snapshot_files)(),
        ]
        diff = get_diff(self.pr_version, self.base_version)
        assert [f.path for f in diff.modified] == ["index.html"]
        assert diff.added == []
        assert diff.deleted == []

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_kept_when_merge_base_unchanged(self, storage_open):
        """No-op when an existing snapshot already matches the current merge-base."""
        storage_open.side_effect = [
            _mock_manifest(self.base_build.id, {"index.html": "h"}, merge_base="abc")(),
        ]
        snapshot_base_manifest(
            self.pr_version, self.base_version, current_merge_base="abc"
        )
        # Single read of the existing snapshot, no write.
        assert storage_open.call_count == 1

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_kept_when_no_current_merge_base(self, storage_open):
        """Graceful fallback: if we don't know the current merge-base, keep the snapshot."""
        storage_open.side_effect = [
            _mock_manifest(self.base_build.id, {"index.html": "h"}, merge_base="abc")(),
        ]
        snapshot_base_manifest(
            self.pr_version, self.base_version, current_merge_base=None
        )
        assert storage_open.call_count == 1

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_refreshed_when_merge_base_changes(self, storage_open):
        """Snapshot is rewritten when current merge-base differs from stored one."""
        write_handle = mock.MagicMock()
        write_cm = mock.MagicMock()
        write_cm.__enter__ = mock.MagicMock(return_value=write_handle)
        write_cm.__exit__ = mock.MagicMock(return_value=False)
        # 1) Read existing snapshot (old merge_base)
        # 2) Read base version's live manifest (new content)
        # 3) Open snapshot path for writing
        storage_open.side_effect = [
            _mock_manifest(self.base_build.id, {"index.html": "old"}, merge_base="old-mb")(),
            _mock_manifest(self.base_build.id, {"index.html": "new"})(),
            write_cm,
        ]

        snapshot_base_manifest(
            self.pr_version, self.base_version, current_merge_base="new-mb"
        )

        assert storage_open.call_count == 3
        assert storage_open.call_args_list[2].args[1] == "w"
        written = "".join(call.args[0] for call in write_handle.write.call_args_list)
        assert '"merge_base": "new-mb"' in written

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_created_when_missing(self, storage_open):
        """First build of a PR creates a snapshot pinned to its merge-base."""
        write_handle = mock.MagicMock()
        write_cm = mock.MagicMock()
        write_cm.__enter__ = mock.MagicMock(return_value=write_handle)
        write_cm.__exit__ = mock.MagicMock(return_value=False)
        # 1) snapshot read miss, 2) live base read, 3) write
        storage_open.side_effect = [
            FileNotFoundError,
            _mock_manifest(self.base_build.id, {"index.html": "h"})(),
            write_cm,
        ]

        snapshot_base_manifest(
            self.pr_version, self.base_version, current_merge_base="mb-1"
        )

        assert storage_open.call_count == 3
        assert storage_open.call_args_list[2].args[1] == "w"
        written = "".join(call.args[0] for call in write_handle.write.call_args_list)
        assert '"merge_base": "mb-1"' in written
