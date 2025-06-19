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
from enum import StrEnum
from enum import auto
from functools import cached_property

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.storage import build_media_storage


MANIFEST_FILE_NAME = "manifest.json"


class FileTreeDiffFileStatus(StrEnum):
    """Status of a file in the file tree diff."""

    ADDED = auto()
    DELETED = auto()
    MODIFIED = auto()

    @property
    def emoji(self):
        """Return an emoji representing the file status."""
        if self == FileTreeDiffFileStatus.ADDED:
            return "➕"
        elif self == FileTreeDiffFileStatus.DELETED:
            return "❌"
        elif self == FileTreeDiffFileStatus.MODIFIED:
            return "📝"
        return ""


class FileTreeDiffFile:
    def __init__(
        self,
        filename: str,
        current_version,
        current_version_build: Build,
        base_version,
        base_version_build: Build,
        status: FileTreeDiffFileStatus,
        resolver: Resolver,
    ):
        self.filename = filename
        self.current_version = current_version
        self.current_version_build = current_version_build
        self.base_version = base_version
        self.base_version_build = base_version_build
        self.status = status
        self._resolver = resolver

    @property
    def url(self):
        return self._resolver.resolve_version(
            project=self.current_version.project,
            version=self.current_version,
            filename=self.filename,
        )

    @property
    def base_url(self):
        return self._resolver.resolve_version(
            project=self.base_version.project,
            version=self.base_version,
            filename=self.filename,
        )


class FileTreeDiff:
    def __init__(
        self,
        current_version: Version,
        base_version: Version,
        current_version_build: Build,
        base_version_build: Build,
        files: list[FileTreeDiffFile],
        outdated: bool,
    ):
        self.current_version = current_version
        self.current_version_build = current_version_build
        self.base_version = base_version
        self.base_version_build = base_version_build
        self.files = files
        self.outdated = outdated
        self._resolver = Resolver()

    @cached_property
    def added(self):
        """List of added files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.ADDED]

    @cached_property
    def deleted(self):
        """List of deleted files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.DELETED]

    @cached_property
    def modified(self):
        """List of modified files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.MODIFIED]

    def top_files(self, limit: int = 5) -> list[FileTreeDiffFile]:
        """Get the top files from all added, deleted, and modified files."""
        added = []
        deleted = []
        modified = []
        while limit > 0:
            if self.added:
                added.append(self.added[len(added)])
                limit -= 1
                if limit <= 0:
                    break

            if self.deleted:
                deleted.append(self.deleted[len(deleted)])
                limit -= 1
                if limit <= 0:
                    break

            if self.modified:
                modified.append(self.modified[len(modified)])
                limit -= 1
                if limit <= 0:
                    break


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

    files = []
    resolver = Resolver()
    for file_path in current_version_file_paths - base_version_file_paths:
        files.append(
            FileTreeDiffFile(
                current_version=current_version,
                current_version_build=current_version_build,
                base_version=base_version,
                base_version_build=base_version_build,
                filename=file_path,
                status=FileTreeDiffFileStatus.ADDED,
                resolver=resolver,
            )
        )

    for file_path in base_version_file_paths - current_version_file_paths:
        files.append(
            FileTreeDiffFile(
                current_version=current_version,
                current_version_build=current_version_build,
                base_version=base_version,
                base_version_build=base_version_build,
                filename=file_path,
                status=FileTreeDiffFileStatus.DELETED,
                resolver=resolver,
            )
        )

    for file_path in current_version_file_paths & base_version_file_paths:
        file_a = current_version_manifest.files[file_path]
        file_b = base_version_manifest.files[file_path]
        if file_a.main_content_hash != file_b.main_content_hash:
            files.append(
                FileTreeDiffFile(
                    current_version=current_version,
                    current_version_build=current_version_build,
                    base_version=base_version,
                    base_version_build=base_version_build,
                    filename=file_path,
                    status=FileTreeDiffFileStatus.MODIFIED,
                    resolver=resolver,
                )
            )

    def sortpath(file):
        """
        Function to use as `key=` argument for `sorted`.

        It sorts the file names by the less deep directories first.
        However, it doesn't group the results by directory.

        Ideally, this should sort file names by hierarchy (less deep directory
        first), groupping them by directory and alphabetically. We should update
        this function to achieve that goal if we find a simple way to do it.
        """
        parts = file.filename.split("/")
        return len(parts), parts

    return FileTreeDiff(
        files=sorted(files, key=sortpath),
        current_version=current_version,
        base_version=base_version,
        current_version_build=current_version_build,
        base_version_build=base_version_build,
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
