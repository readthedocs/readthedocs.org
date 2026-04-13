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
from readthedocs.filetreediff.dataclasses import BaseSnapshot
from readthedocs.filetreediff.dataclasses import FileTreeDiff
from readthedocs.filetreediff.dataclasses import FileTreeDiffFileStatus
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.projects.constants import MEDIA_TYPE_HTML
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

MANIFEST_FILE_NAME = "manifest.json"
BASE_SNAPSHOT_FILE_NAME = "base_snapshot.json"
BASE_HTML_DIR_NAME = "base_html"


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
    outdated = False
    manifests: list[FileTreeDiffManifest] = []
    for version in (current_version, base_version):
        manifest = get_manifest(version)
        if not manifest:
            return None

        latest_build = version.latest_successful_build
        if not latest_build:
            return None

        if latest_build.id != manifest.build.id:
            outdated = True

        manifests.append(manifest)

    # pylint: disable=unbalanced-tuple-unpacking
    current_version_manifest, base_version_manifest = manifests
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


def get_base_snapshot(version: Version) -> BaseSnapshot | None:
    """
    Get the base snapshot for an external (PR) version.

    Returns None if no base snapshot exists yet.
    """
    snapshot_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=BASE_SNAPSHOT_FILE_NAME,
    )
    try:
        with build_media_storage.open(snapshot_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None

    return BaseSnapshot.from_dict(data)


def write_base_snapshot(version: Version, snapshot: BaseSnapshot):
    """Write the base snapshot metadata for an external (PR) version."""
    snapshot_path = version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=BASE_SNAPSHOT_FILE_NAME,
    )
    with build_media_storage.open(snapshot_path, "w") as f:
        json.dump(snapshot.as_dict(), f)


def snapshot_base_html(pr_version: Version, base_version: Version):
    """
    Copy base version's HTML files into the PR version's diff storage.

    Only copies *.html files -- static assets (CSS, JS, images) are not needed
    since visual diff only extracts and compares <main> content from HTML pages.

    Also writes a base_snapshot.json with the base build metadata.
    """
    latest_base_build = base_version.latest_successful_build
    if not latest_base_build:
        log.warning(
            "No successful build for base version, skipping base HTML snapshot.",
            base_version_slug=base_version.slug,
        )
        return

    # Check if a snapshot already exists for this PR version.
    existing_snapshot = get_base_snapshot(pr_version)
    if existing_snapshot is not None:
        log.info(
            "Base HTML snapshot already exists, skipping.",
            pr_version_slug=pr_version.slug,
            base_build_id=existing_snapshot.base_build_id,
        )
        return

    source_path = base_version.get_storage_path(media_type=MEDIA_TYPE_HTML)
    dest_path = pr_version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=BASE_HTML_DIR_NAME,
    )

    log.info(
        "Creating base HTML snapshot for PR version.",
        pr_version_slug=pr_version.slug,
        base_version_slug=base_version.slug,
        base_build_id=latest_base_build.id,
        source_path=source_path,
        dest_path=dest_path,
    )

    build_media_storage.rclone_copy_remote_directory(
        source=source_path,
        destination=dest_path,
        include="*.html",
    )

    snapshot = BaseSnapshot(
        base_build_id=latest_base_build.id,
        base_version_slug=base_version.slug,
    )
    write_base_snapshot(pr_version, snapshot)
