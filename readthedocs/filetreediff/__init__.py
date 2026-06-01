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
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

MANIFEST_FILE_NAME = "manifest.json"
BASE_MANIFEST_SNAPSHOT_FILE_NAME = "base_manifest_snapshot.json"


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
    # (pinned at first PR build, refreshed when the PR's merge-base advances)
    # over the live base manifest. This prevents false positives when the
    # base branch has moved forward since the PR was created. Falls back to
    # the live manifest if no snapshot exists.
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

    current_version_file_paths = set(current_version_manifest.files.keys())
    base_version_file_paths = set(base_version_manifest.files.keys())

    current_version_build = Build.objects.get(id=current_version_manifest.build.id)
    base_version_build = Build.objects.get(id=base_version_manifest.build.id)

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


def snapshot_base_manifest(
    external_version: Version,
    base_version: Version,
    force_refresh: bool = False,
):
    """
    Snapshot the base version's current manifest for a PR version.

    By default (``force_refresh=False``), only writes if no snapshot exists
    yet (first build of the PR). When called with ``force_refresh=True``,
    rewrites the snapshot with the base version's current manifest — used by
    ``refresh_snapshot_if_stale`` after detecting that the PR's merge-base
    has advanced.

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
    if not force_refresh and build_media_storage.exists(snapshot_path):
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
        force_refresh=force_refresh,
    )


def should_refresh_snapshot(external_version: Version, vcs_repository) -> bool:
    """
    Return True iff the PR's snapshot has fallen behind its merge-base.

    The merge-base is computed against the project's default branch using the
    live VCS clone. Any missing data or git failure returns False so the
    existing snapshot is preserved.
    """
    snapshot = _get_base_manifest_snapshot(external_version)
    if snapshot is None:
        # First PR build; the indexer will create the snapshot on success.
        return False

    snap_commit = (
        Build.objects.filter(id=snapshot.build.id)
        .values_list("commit", flat=True)
        .first()
    )
    if not snap_commit:
        return False

    base_branch = external_version.project.get_default_branch()
    if not base_branch:
        return False

    base_ref = f"refs/remotes/origin/{base_branch}"
    try:
        code, _, _ = vcs_repository.run(
            "git",
            "fetch",
            "--depth",
            "50",
            "origin",
            f"refs/heads/{base_branch}:{base_ref}",
            record=False,
        )
        if code != 0:
            return False

        code, mb_stdout, _ = vcs_repository.run(
            "git", "merge-base", "HEAD", base_ref, record=False
        )
        if code != 0:
            return False

        code, _, _ = vcs_repository.run(
            "git",
            "merge-base",
            "--is-ancestor",
            snap_commit,
            mb_stdout.strip(),
            record=False,
        )
    except RepositoryError:
        return False

    # 0 = snap still in sync; 1 = needs refresh; anything else = stay conservative.
    return code == 1


def refresh_snapshot_if_stale(external_version: Version, vcs_repository) -> None:
    """
    Rewrite the PR's base manifest snapshot if the merge-base has advanced.

    Best-effort: any failure is swallowed and the existing snapshot (if any)
    is left in place. No-op when no snapshot exists yet — the indexer
    creates it on first PR build.

    Must be called while the VCS clone is live (i.e. inside the build
    task's VCS environment context).
    """
    if not external_version.is_external:
        return
    try:
        base_version = external_version.get_base_version_for_diff()
        if not base_version:
            return
        if should_refresh_snapshot(external_version, vcs_repository):
            snapshot_base_manifest(
                external_version, base_version, force_refresh=True
            )
    except Exception:
        log.exception(
            "Filetreediff snapshot refresh check failed.",
            project_slug=external_version.project.slug,
            version_slug=external_version.slug,
        )
