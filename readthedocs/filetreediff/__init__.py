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
from difflib import SequenceMatcher

import structlog

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.filetreediff.dataclasses import FileTreeDiff
from readthedocs.filetreediff.dataclasses import FileTreeDiffFileStatus
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.projects.models import Project
from readthedocs.search.parsers import GenericParser
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

MANIFEST_FILE_NAME = "manifest.json"
BASE_MANIFEST_SNAPSHOT_FILE_NAME = "base_manifest_snapshot.json"
MAX_FILES_TO_COUNT_CHANGED_BLOCKS = 100


def get_base_version(project: Project) -> Version | None:
    """
    Get the version to diff against for a project.

    This is the version configured in the addons settings,
    or ``latest`` if none is configured.

    Return ``None`` if the version doesn't exist,
    or if it isn't active and built, since there is nothing usable
    to compare against in that case.
    """
    base_version = project.addons.options_base_version or project.get_latest_version()
    if not _is_usable_base_version(base_version):
        return None
    return base_version


def _is_usable_base_version(version: Version | None) -> bool:
    if not version:
        return False
    if not version.active or not version.built:
        log.debug(
            "Base version isn't active or built, skipping file tree diff.",
            project_slug=version.project.slug,
            base_version_slug=version.slug,
            active=version.active,
            built=version.built,
        )
        return False
    return True


def get_diff(current_version: Version, base_version: Version) -> FileTreeDiff | None:
    """
    Get the file tree diff between two versions.

    If the base version isn't active and built, return None.
    If any of the versions don't have a manifest, return None.
    If the latest build of any of the versions is different from the manifest build,
    the diff is marked as outdated. The client is responsible for deciding
    how to handle this case.

    Set operations are used to calculate the added, deleted, and modified files.
    To get the modified files, we compare the main content hash of each common file.
    If there are no changes between the versions, all lists will be empty.
    """
    if not _is_usable_base_version(base_version):
        return None

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

    current_version_file_paths = set(current_version_manifest.files.keys())
    base_version_file_paths = set(base_version_manifest.files.keys())

    current_version_build = Build.objects.get(id=current_version_manifest.build.id)
    base_version_build = Build.objects.get(id=base_version_manifest.build.id)

    files: list[tuple[str, FileTreeDiffFileStatus]] = []
    changed_blocks: dict[str, int] = {}
    for file_path in current_version_file_paths - base_version_file_paths:
        files.append((file_path, FileTreeDiffFileStatus.added))

    for file_path in base_version_file_paths - current_version_file_paths:
        files.append((file_path, FileTreeDiffFileStatus.deleted))

    for file_path in current_version_file_paths & base_version_file_paths:
        file_a = current_version_manifest.files[file_path]
        file_b = base_version_manifest.files[file_path]
        if file_a.text_hash and file_b.text_hash:
            modified = file_a.text_hash != file_b.text_hash
        else:
            # One of the manifests was written before we hashed the text of
            # the page, so ``main_content_hash`` is all both sides have. It
            # reports pages as modified when only their attributes changed.
            # TODO: remove this branch and ``main_content_hash`` itself once
            # no manifest in storage is missing a text hash. ``markup_hash``
            # replaces it, see https://github.com/readthedocs/readthedocs.org/issues/13258
            modified = file_a.main_content_hash != file_b.main_content_hash
        if modified:
            files.append((file_path, FileTreeDiffFileStatus.modified))
            if file_a.changed_blocks is not None:
                changed_blocks[file_path] = file_a.changed_blocks

    return FileTreeDiff(
        files=files,
        current_version=current_version,
        current_version_build=current_version_build,
        base_version=base_version,
        base_version_build=base_version_build,
        outdated=outdated,
        changed_blocks=changed_blocks,
    )


def add_changed_blocks(manifest: FileTreeDiffManifest, version: Version, base_version: Version):
    """
    Set the number of changed blocks on each modified file of the manifest.

    Only files whose text changed are parsed again, from both versions.
    Nothing is counted when too many files changed, since each one is read
    twice from storage. Files without a count keep their path order.
    """
    base_manifest = _get_base_manifest_snapshot(version) or get_manifest(base_version)
    if not base_manifest:
        return

    modified_files = []
    for path, file in manifest.files.items():
        base_file = base_manifest.files.get(path)
        if base_file and base_file.text_hash != file.text_hash:
            modified_files.append(file)

    if len(modified_files) > MAX_FILES_TO_COUNT_CHANGED_BLOCKS:
        log.info(
            "Too many modified files, not counting changed blocks.",
            project_slug=version.project.slug,
            version_slug=version.slug,
            modified_files=len(modified_files),
        )
        return

    parser = GenericParser(version)
    base_parser = GenericParser(base_version)
    for file in modified_files:
        try:
            file.changed_blocks = count_changed_blocks(
                base_parser.get_blocks(file.path),
                parser.get_blocks(file.path),
            )
        except Exception:
            # The count only sorts the list, never fail the manifest for it.
            log.warning("Failed to count changed blocks.", path=file.path, exc_info=True)


def count_changed_blocks(base_blocks: list[str], blocks: list[str]) -> int:
    """
    Count the blocks that changed between two versions of a file.

    The blocks are aligned first, so adding a paragraph counts as one change,
    instead of changing every block after it. A block edited in place counts once.
    """
    matcher = SequenceMatcher(a=base_blocks, b=blocks, autojunk=False)
    changed = 0
    for operation, base_start, base_end, start, end in matcher.get_opcodes():
        if operation != "equal":
            changed += max(base_end - base_start, end - start)
    return changed


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
