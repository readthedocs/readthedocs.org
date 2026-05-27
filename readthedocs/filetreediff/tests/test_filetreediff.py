import json
from contextlib import contextmanager
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
    EXTERNAL,
    LATEST,
)
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff import (
    delete_manifest_for_build,
    get_diff_for_build,
    get_manifest_for_build,
    resolve_pr_diff_base_build,
    write_manifest,
)
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest


@contextmanager
def _mock_read(content):
    read_mock = mock.MagicMock()
    read_mock.read.return_value = content
    yield read_mock


def _manifest_payload(files: dict[str, str]) -> str:
    return json.dumps(
        {
            "files": {
                path: {"main_content_hash": content_hash}
                for path, content_hash in files.items()
            },
        }
    )


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsGetDiffForBuildNormalVersion(TestCase):
    """Normal version builds are diffed against the previous successful build."""

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
    def test_diff_against_previous_build(self, storage_open):
        current_files = {"index.html": "hash1", "new.html": "hash-new"}
        previous_files = {"index.html": "hash0", "old.html": "hash-old"}
        storage_open.side_effect = [
            _mock_read(_manifest_payload(current_files)),
            _mock_read(_manifest_payload(previous_files)),
        ]
        diff = get_diff_for_build(self.latest_build)
        assert [f.path for f in diff.added] == ["new.html"]
        assert [f.path for f in diff.deleted] == ["old.html"]
        assert [f.path for f in diff.modified] == ["index.html"]
        assert not diff.outdated

    def test_returns_none_for_failed_build(self):
        failed_build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=False,
        )
        assert get_diff_for_build(failed_build) is None

    def test_returns_none_for_unfinished_build(self):
        running_build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_TRIGGERED,
            success=True,
        )
        assert get_diff_for_build(running_build) is None

    def test_returns_none_when_no_previous_build_exists(self):
        # `previous_build` and `latest_build` exist for self.version, but
        # a fresh version with only one build has no prior build to diff against.
        new_version = get(Version, project=self.project, slug="brand-new", active=True, built=True)
        only_build = get(
            Build,
            project=self.project,
            version=new_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        assert get_diff_for_build(only_build) is None

    def test_returns_none_for_versionless_build(self):
        orphan_build = get(Build, project=self.project, version=None)
        assert get_diff_for_build(orphan_build) is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_returns_none_when_current_manifest_missing(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        assert get_diff_for_build(self.latest_build) is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_returns_none_when_base_manifest_missing(self, storage_open):
        storage_open.side_effect = [
            _mock_read(_manifest_payload({"index.html": "hash1"})),
            FileNotFoundError,
        ]
        assert get_diff_for_build(self.latest_build) is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_skips_failed_builds_when_resolving_base(self, storage_open):
        """A failed build in between shouldn't be picked as the base."""
        failed_in_between = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=False,
        )
        newer_success = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        # Sanity: id ordering matches setUp creation order
        assert self.previous_build.id < self.latest_build.id < failed_in_between.id < newer_success.id

        storage_open.side_effect = [
            _mock_read(_manifest_payload({"a.html": "h1"})),
            _mock_read(_manifest_payload({"a.html": "h0"})),
        ]
        diff = get_diff_for_build(newer_success)
        # Base should be `self.latest_build` (most recent successful, skipping `failed_in_between`).
        assert diff.base_version_build.id == self.latest_build.id


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsGetDiffForBuildPRVersion(TestCase):
    """PR builds are diffed against the pinned ``diff_base_build``."""

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
            diff_base_build=self.base_build,
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_diff_uses_pinned_base_build(self, storage_open):
        pr_files = {"index.html": "pr-hash", "new-page.html": "new-hash"}
        base_files = {"index.html": "original-hash"}
        storage_open.side_effect = [
            _mock_read(_manifest_payload(pr_files)),
            _mock_read(_manifest_payload(base_files)),
        ]
        diff = get_diff_for_build(self.pr_build)
        assert [f.path for f in diff.added] == ["new-page.html"]
        assert [f.path for f in diff.modified] == ["index.html"]
        assert diff.deleted == []
        assert diff.base_version_build.id == self.base_build.id
        assert diff.current_version_build.id == self.pr_build.id

    def test_returns_none_when_pr_build_has_no_pinned_base(self):
        unpinned = get(
            Build,
            project=self.project,
            version=self.pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
            diff_base_build=None,
        )
        assert get_diff_for_build(unpinned) is None


class TestsResolvePRDiffBaseBuild(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.base_version = self.project.versions.get(slug=LATEST)
        self.base_build_old = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.base_build_latest = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.pr_version = get(
            Version,
            project=self.project,
            slug="pr-7",
            type=EXTERNAL,
            active=True,
            built=True,
        )

    def test_first_pr_build_pins_to_base_version_latest(self):
        first_pr_build = get(
            Build,
            project=self.project,
            version=self.pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        resolved = resolve_pr_diff_base_build(self.pr_version, first_pr_build)
        assert resolved.id == self.base_build_latest.id

    def test_subsequent_pr_build_inherits_pin_from_prior(self):
        # First PR build pinned to an older base build.
        get(
            Build,
            project=self.project,
            version=self.pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
            diff_base_build=self.base_build_old,
        )
        # Base version has moved on — a newer base build exists.
        get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        second_pr_build = get(
            Build,
            project=self.project,
            version=self.pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        resolved = resolve_pr_diff_base_build(self.pr_version, second_pr_build)
        # Inherits the prior PR build's pin, not the base version's new latest.
        assert resolved.id == self.base_build_old.id

    def test_returns_none_when_base_version_has_no_successful_build(self):
        empty_base_project = get(Project)
        # No successful build for the project's base version.
        pr_version = get(
            Version,
            project=empty_base_project,
            slug="pr-1",
            type=EXTERNAL,
            active=True,
            built=True,
        )
        first_pr_build = get(
            Build,
            project=empty_base_project,
            version=pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        assert resolve_pr_diff_base_build(pr_version, first_pr_build) is None


@mock.patch(
    "readthedocs.filetreediff.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestsWriteAndDeleteManifest(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug=LATEST)
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_write_manifest_uses_per_build_path(self, storage_open):
        writes = []

        @contextmanager
        def write_capture(path, mode):
            write_capture.path = path
            write_capture.mode = mode
            write_mock = mock.MagicMock()
            write_mock.write.side_effect = writes.append
            yield write_mock

        storage_open.side_effect = write_capture
        write_manifest(self.build, {"index.html": "hash1", "guide.html": "hash2"})

        expected_suffix = f"builds/{self.build.id}/manifest.json"
        assert write_capture.path.endswith(expected_suffix)
        assert write_capture.mode == "w"

        written = json.loads("".join(writes))
        assert set(written["files"].keys()) == {"index.html", "guide.html"}
        assert written["files"]["index.html"]["main_content_hash"] == "hash1"

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_get_manifest_for_build_returns_none_when_missing(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        assert get_manifest_for_build(self.build) is None

    @mock.patch.object(BuildMediaFileSystemStorageTest, "delete")
    def test_delete_manifest_for_build_targets_per_build_path(self, storage_delete):
        delete_manifest_for_build(self.build)
        storage_delete.assert_called_once()
        target = storage_delete.call_args.args[0]
        assert target.endswith(f"builds/{self.build.id}/manifest.json")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "delete")
    def test_delete_manifest_for_build_no_op_without_version(self, storage_delete):
        orphan = get(Build, project=self.project, version=None)
        delete_manifest_for_build(orphan)
        storage_delete.assert_not_called()
