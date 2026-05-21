import json
from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff import (
    get_diff,
    get_diff_for_build,
    snapshot_base_manifest,
    snapshot_previous_manifest,
)
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

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_get_diff_for_build_uses_base_snapshot(self, storage_open):
        """For PR builds, get_diff_for_build compares against the base version."""
        pr_files = {"index.html": "pr-hash", "new-page.html": "new-hash"}
        snapshot_files = {"index.html": "original-hash"}

        # get_diff reads: 1) PR manifest, 2) base snapshot
        storage_open.side_effect = [
            _mock_manifest(self.pr_build.id, pr_files)(),
            _mock_manifest(self.base_build.id, snapshot_files)(),
        ]
        diff = get_diff_for_build(self.pr_build)
        assert [f.path for f in diff.added] == ["new-page.html"]
        assert [f.path for f in diff.modified] == ["index.html"]
        assert diff.deleted == []


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsPreviousManifestSnapshot(TestCase):
    """Tests for comparing a normal version against its own previous build."""

    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug=LATEST)
        self.previous_build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.latest_build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_uses_previous_manifest_snapshot(self, storage_open):
        """A normal version is compared against its previous build's manifest."""
        current_files = {"index.html": "hash1", "new.html": "hash-new"}
        previous_files = {"index.html": "hash0"}

        # get_diff reads: 1) current manifest, 2) previous manifest snapshot
        storage_open.side_effect = [
            _mock_manifest(self.latest_build.id, current_files)(),
            _mock_manifest(self.previous_build.id, previous_files)(),
        ]
        diff = get_diff(self.version, self.version)
        assert [f.path for f in diff.added] == ["new.html"]
        assert [f.path for f in diff.modified] == ["index.html"]
        assert diff.deleted == []
        assert not diff.outdated

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_falls_back_to_live_manifest_when_no_snapshot(self, storage_open):
        """Without a snapshot, the diff against the same version has no changes."""
        files = {"index.html": "hash1"}

        # get_diff reads: 1) current manifest, 2) snapshot miss, 3) live manifest
        storage_open.side_effect = [
            _mock_manifest(self.latest_build.id, files)(),
            FileNotFoundError,
            _mock_manifest(self.latest_build.id, files)(),
        ]
        diff = get_diff(self.version, self.version)
        assert diff.files == []

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_previous_manifest_copies_current_manifest(self, storage_open):
        """snapshot_previous_manifest writes a copy of the current manifest."""
        current_files = {"index.html": "hash1", "guide.html": "hash2"}
        writes = []

        @contextmanager
        def write_capture(*args, **kwargs):
            write_mock = mock.MagicMock()
            write_mock.write.side_effect = writes.append
            yield write_mock

        storage_open.side_effect = [
            _mock_manifest(self.latest_build.id, current_files)(),
            write_capture(),
        ]
        snapshot_previous_manifest(self.version)

        assert storage_open.call_count == 2
        written = json.loads("".join(writes))
        assert written["build"]["id"] == self.latest_build.id
        assert set(written["files"].keys()) == {"index.html", "guide.html"}

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_snapshot_previous_manifest_noop_without_manifest(self, storage_open):
        """snapshot_previous_manifest does nothing if there is no manifest yet."""
        storage_open.side_effect = FileNotFoundError
        snapshot_previous_manifest(self.version)
        storage_open.assert_called_once()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_get_diff_for_build_uses_previous_manifest_snapshot(self, storage_open):
        """For normal version builds, get_diff_for_build compares previous builds."""
        current_files = {"index.html": "hash1", "new.html": "hash-new"}
        previous_files = {"index.html": "hash1"}

        storage_open.side_effect = [
            _mock_manifest(self.latest_build.id, current_files)(),
            _mock_manifest(self.previous_build.id, previous_files)(),
        ]
        diff = get_diff_for_build(self.latest_build)
        assert [f.path for f in diff.added] == ["new.html"]
        assert diff.modified == []
        assert diff.deleted == []
