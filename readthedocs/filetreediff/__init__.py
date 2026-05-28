"""
Module for the file tree diff feature (FTD).

This feature is used to compare the files of two versions of a project.

The process is as follows:

- A build is triggered for a version.
- A task is triggered after the build has succeeded
  to generate a manifest of the files of the version.
  Currently, we only consider the latest version and pull request previews.
- The manifest contains the hash of the main content of each file.
  Only HTML files are considered for now.
- The manifest is stored in the diff media storage.
- Then our application can compare the manifest to get a list of added,
  deleted, and modified files between two versions.
"""

import json

import structlog

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.filetreediff.dataclasses import FileTreeDiff
from readthedocs.filetreediff.dataclasses import FileTreeDiffFileStatus
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

MANIFEST_FILE_NAME = "manifest.json"
BASE_MANIFEST_SNAPSHOT_FILE_NAME = "base_manifest_snapshot.json"
PREVIOUS_MANIFEST_SNAPSHOT_FILE_NAME = "previous_manifest_snapshot.json"


def get_diff_base_version(project):
    """
    Resolve the base version a PR's diff should be compared against.

    Falls back to the project's latest version if no explicit base is
    configured. Returns ``None`` if no base version can be determined.
    """
    return project.addons.options_base_version or project.get_latest_version()


def get_diff(current_version: Version, base_version: Version) -> FileTreeDiff | None:
    """
    Get the file tree diff between two versions.

    If any of the versions don't have a manifest, return None.
    If the latest build of any of the versions is different from the manifest build,
    the diff is marked as outdated. The client is responsible for deciding
    how to handle this case.

    Set operations are used to calculate the added, deleted, and modified files.
    To get the modified files, we compare the main content hash of each common file.
    If there are no changes between the versions, all lists will be empty.
    """
    current_version_manifest = get_manifest(current_version)
    if not current_version_manifest:
        return None

    current_latest_build = current_version.latest_successful_build
    if not current_latest_build:
        return None

    outdated = current_latest_build.id != current_version_manifest.build.id

    # For external versions (PRs), prefer the snapshotted base manifest
    # (pinned at first PR build) over the live base manifest. This prevents
    # false positives when the base branch has moved forward since the PR was
    # created. Falls back to the live manifest if no snapshot exists.
    # TODO: call clear_base_manifest_snapshot() on PR rebase/synchronize
    # events so the snapshot is refreshed against the new base.
    #
    # When a snapshot is used, we intentionally skip the base-side `outdated`
    # check. The snapshot's build will be older than the base version's latest
    # build (the base branch kept moving) — that's the whole point. Marking
    # the diff as outdated here would defeat the snapshot's purpose.
    base_version_manifest = None
    if current_version.is_external:
        base_version_manifest = _get_base_manifest_snapshot(current_version)

    if not base_version_manifest:
        base_version_manifest = get_manifest(base_version)
        if not base_version_manifest:
            return None

        base_latest_build = base_version.latest_successful_build
        if not base_latest_build:
            return None

        if base_latest_build.id != base_version_manifest.build.id:
            outdated = True

    return _build_diff(
        current_version=current_version,
        current_version_manifest=current_version_manifest,
        base_version=base_version,
        base_version_manifest=base_version_manifest,
        outdated=outdated,
    )


def _build_diff(
    *,
    current_version: Version,
    current_version_manifest: FileTreeDiffManifest,
    base_version: Version,
    base_version_manifest: FileTreeDiffManifest,
    outdated: bool,
) -> FileTreeDiff | None:
    """
    Construct a :class:`FileTreeDiff` from two resolved manifests.

    Returns ``None`` if either manifest's referenced Build row has been
    deleted (e.g. by ``delete_old_build_objects``). The diff would otherwise
    crash with ``Build.DoesNotExist``.
    """
    current_version_build = Build.objects.filter(
        id=current_version_manifest.build.id
    ).first()
    base_version_build = Build.objects.filter(
        id=base_version_manifest.build.id
    ).first()
    if not current_version_build or not base_version_build:
        return None

    current_version_file_paths = set(current_version_manifest.files.keys())
    base_version_file_paths = set(base_version_manifest.files.keys())

    files: list[tuple[str, FileTreeDiffFileStatus]] = []
    for file_path in current_version_file_paths - base_version_file_paths:
        files.append((file_path, FileTreeDiffFileStatus.added))

    for file_path in base_version_file_paths - current_version_file_paths:
        files.append((file_path, FileTreeDiffFileStatus.deleted))

    for file_path in current_version_file_paths & base_version_file_paths:
        file_a = current_version_manifest.files[file_path]
        file_b = base_version_manifest.files[file_path]
        if file_a.main_content_hash != file_b.main_content_hash:
            files.append((file_path, FileTreeDiffFileStatus.modified))

    return FileTreeDiff(
        files=files,
        current_version=current_version,
        current_version_build=current_version_build,
        base_version=base_version,
        base_version_build=base_version_build,
        outdated=outdated,
    )


def get_diff_for_build(build: Build) -> FileTreeDiff | None:
    """
    Get the file tree diff for a build, picking the right base to compare against.

    Pull request builds are compared against the project's base version (the
    latest version by default). Normal version builds are compared against the
    version's own previous build, using the manifest snapshot taken before the
    current build overwrote the version's manifest.

    Returns ``None`` if the build didn't finish successfully, isn't the
    version's latest successful build (manifests are per-version and represent
    only the latest build), has no version, or has no diff available.
    """
    if not build.success or not build.finished:
        return None

    version = build.version
    if not version:
        return None

    # Manifests are stored per-version and overwritten by each new build, so
    # they only represent the latest successful build. Computing a diff for an
    # older build would silently return the latest build's diff, which is
    # misleading on a historical build's detail page.
    latest = version.latest_successful_build
    if not latest or latest.id != build.id:
        return None

    if version.is_external:
        base_version = get_diff_base_version(build.project)
        if not base_version:
            return None
        return get_diff(current_version=version, base_version=base_version)

    return _get_diff_against_previous_build(version)


def _get_diff_against_previous_build(version: Version) -> FileTreeDiff | None:
    """
    Diff the version's latest manifest against its own previous-build snapshot.

    Used for non-PR builds. Returns ``None`` when no previous snapshot exists
    (e.g. the very first build of the version).
    """
    current_manifest = get_manifest(version)
    if not current_manifest:
        return None
    previous_manifest = _get_previous_manifest_snapshot(version)
    if not previous_manifest:
        return None
    return _build_diff(
        current_version=version,
        current_version_manifest=current_manifest,
        base_version=version,
        base_version_manifest=previous_manifest,
        outdated=False,
    )


def get_manifest(version: Version) -> FileTreeDiffManifest | None:
    """
    Get the file manifest for a version.

    If the manifest file does not exist, return None.
    """
    manifest_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=MANIFEST_FILE_NAME,
    )
    try:
        with build_media_storage.open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)
    except FileNotFoundError:
        return None

    return FileTreeDiffManifest.from_dict(manifest)


def write_manifest(version: Version, manifest: FileTreeDiffManifest):
    manifest_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=MANIFEST_FILE_NAME,
    )
    with build_media_storage.open(manifest_path, "w") as f:
        json.dump(manifest.as_dict(), f)


def _get_base_manifest_snapshot(
    external_version: Version,
) -> FileTreeDiffManifest | None:
    """Get the snapshotted base manifest for an external version, or None."""
    snapshot_path = external_version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=BASE_MANIFEST_SNAPSHOT_FILE_NAME,
    )
    try:
        with build_media_storage.open(snapshot_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None

    return FileTreeDiffManifest.from_dict(data)


def snapshot_base_manifest(external_version: Version, base_version: Version):
    """
    Snapshot the base version's current manifest for a PR version.

    Only writes if no snapshot exists yet (first build of the PR).

    This stores a full copy of the base manifest per PR. If many PRs branch
    from the same base commit, the same content is duplicated. This is a
    deliberate tradeoff: manifests are small (a few KB–hundreds of KB), and
    the full-copy approach means cleanup is free (deleting the PR's storage
    directory removes the snapshot too — no reference counting needed).

    A future optimization could store manifests keyed by commit hash
    (``manifests/{commit}.json``) and have the snapshot be a pointer. This
    would dedup storage but requires a GC task to clean up unreferenced
    manifests. Same approach could extend to all build artifacts if we move
    toward content-addressed storage.
    """
    snapshot_path = external_version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=BASE_MANIFEST_SNAPSHOT_FILE_NAME,
    )
    if build_media_storage.exists(snapshot_path):
        return

    base_manifest = get_manifest(base_version)
    if not base_manifest:
        return

    with build_media_storage.open(snapshot_path, "w") as f:
        json.dump(base_manifest.as_dict(), f)

    log.info(
        "Base manifest snapshot created.",
        project_slug=external_version.project.slug,
        external_version_slug=external_version.slug,
        base_version_slug=base_version.slug,
        base_build_id=base_manifest.build.id,
    )
    # TODO: add a clear_base_manifest_snapshot() helper and call it on PR
    # rebase/synchronize webhook events so the snapshot refreshes when the
    # PR is rebased against a newer base.
    # See https://github.com/readthedocs/readthedocs.org/issues/12232


def _get_previous_manifest_snapshot(version: Version) -> FileTreeDiffManifest | None:
    """Get the manifest snapshot from before the version's latest build, or None."""
    snapshot_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=PREVIOUS_MANIFEST_SNAPSHOT_FILE_NAME,
    )
    try:
        with build_media_storage.open(snapshot_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None

    return FileTreeDiffManifest.from_dict(data)


def snapshot_previous_manifest(version: Version, new_build_id: int | None = None):
    """
    Snapshot a version's current manifest before it is overwritten.

    This is called before writing the manifest for a new build of a normal
    version, so the file tree diff can compare the new build against the
    version's previous build.

    Unlike :func:`snapshot_base_manifest`, this overwrites any existing
    snapshot, so it always reflects the build right before the latest one.

    If ``new_build_id`` is provided and matches the existing manifest's
    build id (e.g. on a re-index of the same build, or a re-run that reuses
    the same Build row), the snapshot is *not* refreshed — refreshing would
    overwrite the previous baseline with the current build's own manifest,
    making the next diff empty.
    """
    current_manifest = get_manifest(version)
    if not current_manifest:
        return

    if new_build_id is not None and current_manifest.build.id == new_build_id:
        return

    snapshot_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=PREVIOUS_MANIFEST_SNAPSHOT_FILE_NAME,
    )
    with build_media_storage.open(snapshot_path, "w") as f:
        json.dump(current_manifest.as_dict(), f)

    log.info(
        "Previous manifest snapshot created.",
        project_slug=version.project.slug,
        version_slug=version.slug,
        previous_build_id=current_manifest.build.id,
    )
