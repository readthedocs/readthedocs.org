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

from readthedocs.builds.models import Version
from readthedocs.filetreediff.dataclasses import FileTreeDiff, FileTreeDiffManifest
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.storage import build_media_storage

MANIFEST_FILE_NAME = "manifest.json"


def get_diff(version_a: Version, version_b: Version) -> FileTreeDiff | None:
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
    for version in (version_a, version_b):
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
    version_a_manifest, version_b_manifest = manifests
    files_a = set(version_a_manifest.files.keys())
    files_b = set(version_b_manifest.files.keys())

    files_added = list(files_a - files_b)
    files_deleted = list(files_b - files_a)
    files_modified = []
    for file_path in files_a & files_b:
        file_a = version_a_manifest.files[file_path]
        file_b = version_b_manifest.files[file_path]
        if file_a.main_content_hash != file_b.main_content_hash:
            files_modified.append(file_path)

    def sortpath(filename):
        """
        Function to use as `key=` argument for `sorted`.

        It sorts the file names by the less deep directories first.
        However, it doesn't group the results by directory.

        Ideally, this should sort file names by hierarchy (less deep directory
        first), groupping them by directory and alphabetically. We should update
        this function to achieve that goal if we find a simple way to do it.
        """
        parts = filename.split("/")
        return len(parts), parts

    return FileTreeDiff(
        added=sorted(files_added, key=sortpath),
        deleted=sorted(files_deleted, key=sortpath),
        modified=sorted(files_modified, key=sortpath),
        outdated=outdated,
    )


def get_manifest(version: Version) -> FileTreeDiffManifest | None:
    """
    Get the file manifest for a version.

    If the manifest file does not exist, return None.
    """
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_DIFF,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, MANIFEST_FILE_NAME)
    try:
        with build_media_storage.open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)
    except FileNotFoundError:
        return None

    return FileTreeDiffManifest.from_dict(manifest)


def write_manifest(version: Version, manifest: FileTreeDiffManifest):
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_DIFF,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, MANIFEST_FILE_NAME)
    with build_media_storage.open(manifest_path, "w") as f:
        json.dump(manifest.as_dict(), f)
