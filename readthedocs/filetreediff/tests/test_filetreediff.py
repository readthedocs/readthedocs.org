import json
from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff import (
    get_diff,
    should_refresh_snapshot,
    snapshot_base_manifest,
)
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest


def _mock_open(content):
    @contextmanager
    def f(*args, **kwargs):
        read_mock = mock.MagicMock()
        read_mock.read.return_value = content
        yield read_mock

    return f


def _mock_manifest(build_id: int, files: dict[str, str]):
    return _mock_open(
        json.dumps(
            {
                "build": {"id": build_id},
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

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists", return_value=True)
    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_is_write_once(self, storage_open, storage_exists):
        """snapshot_base_manifest is a no-op if a snapshot already exists."""
        snapshot_base_manifest(self.pr_version, self.base_version)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists", return_value=True)
    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_force_refresh_overwrites_existing_snapshot(self, storage_open, storage_exists):
        """``force_refresh=True`` bypasses the write-once early-return."""
        base_files = {"index.html": "fresh-hash"}

        @contextmanager
        def _write_cm(*args, **kwargs):
            yield mock.MagicMock()

        storage_open.side_effect = [
            _mock_manifest(self.base_build.id, base_files)(),
            _write_cm(),
        ]
        snapshot_base_manifest(
            self.pr_version, self.base_version, force_refresh=True
        )
        # Two calls: read live base manifest, then write snapshot.
        assert storage_open.call_count == 2

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists", return_value=True)
    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_force_refresh_noop_when_base_manifest_missing(self, storage_open, storage_exists):
        """If the live base manifest is missing, no write happens."""
        storage_open.side_effect = FileNotFoundError
        snapshot_base_manifest(
            self.pr_version, self.base_version, force_refresh=True
        )
        # Only the read attempt; no second open() for the write.
        assert storage_open.call_count == 1


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsShouldRefreshSnapshot(TestCase):
    """Tests for the merge-base-aware snapshot refresh decision."""

    def setUp(self):
        self.project = get(Project, default_branch="main")
        self.base_version = self.project.versions.get(slug=LATEST)
        self.snap_build = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
            commit="snap-sha",
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
        self.vcs_repository = mock.MagicMock()
        # Default script: fetch ok, merge-base ok with sha, is-ancestor ok.
        self.vcs_repository.run.side_effect = [
            (0, "", ""),
            (0, "mb-sha\n", ""),
            (0, "", ""),
        ]

    def _snapshot_mock(self, build_id):
        return _mock_manifest(build_id, {"index.html": "h"})()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_no_existing_snapshot_returns_false(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        self.vcs_repository.run.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snap_build_missing_returns_false(self, storage_open):
        storage_open.side_effect = [self._snapshot_mock(999999)]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        self.vcs_repository.run.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snap_build_commit_null_returns_false(self, storage_open):
        self.snap_build.commit = None
        self.snap_build.save()
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        self.vcs_repository.run.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_default_branch_missing_returns_false(self, storage_open):
        self.project.default_branch = None
        self.project.save()
        # Ensure the VCS-fallback path also yields None.
        with mock.patch.object(Project, "get_default_branch", return_value=None):
            storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
            assert (
                should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
            )
        self.vcs_repository.run.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_fetch_failure_returns_false(self, storage_open):
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = [(1, "", "boom")]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        assert self.vcs_repository.run.call_count == 1

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_merge_base_failure_returns_false(self, storage_open):
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = [
            (0, "", ""),
            (128, "", "fatal"),
        ]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        assert self.vcs_repository.run.call_count == 2

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snap_is_ancestor_returns_false(self, storage_open):
        """is-ancestor exit 0 means snap is still in sync; no refresh."""
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
        assert self.vcs_repository.run.call_count == 3

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snap_not_ancestor_returns_true(self, storage_open):
        """is-ancestor exit 1 means merge-base advanced past snap; refresh."""
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = [
            (0, "", ""),
            (0, "mb-sha\n", ""),
            (1, "", ""),
        ]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is True

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snap_unknown_to_clone_returns_false(self, storage_open):
        """is-ancestor exit 128 (commit unknown) is conservative — no refresh."""
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = [
            (0, "", ""),
            (0, "mb-sha\n", ""),
            (128, "", "fatal: Not a valid commit"),
        ]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_repository_error_returns_false(self, storage_open):
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = RepositoryError(
            message_id=RepositoryError.GENERIC
        )
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_empty_merge_base_output_returns_false(self, storage_open):
        storage_open.side_effect = [self._snapshot_mock(self.snap_build.id)]
        self.vcs_repository.run.side_effect = [
            (0, "", ""),
            (0, "   \n", ""),
        ]
        assert should_refresh_snapshot(self.pr_version, self.vcs_repository) is False
