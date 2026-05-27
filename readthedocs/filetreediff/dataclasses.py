import fnmatch
from dataclasses import asdict
from dataclasses import dataclass
from enum import StrEnum
from enum import auto
from functools import cached_property
from typing import Iterator

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver


@dataclass(slots=True)
class FileTreeDiffManifestFile:
    """A file in a file tree manifest."""

    path: str
    main_content_hash: str


@dataclass(slots=True)
class FileTreeDiffManifest:
    """Files captured for a single build.

    The owning build is encoded in the storage path, not in the manifest body.
    """

    files: dict[str, FileTreeDiffManifestFile]

    def __init__(self, files: list[FileTreeDiffManifestFile]):
        self.files = {file.path: file for file in files}

    @classmethod
    def from_dict(cls, data: dict) -> "FileTreeDiffManifest":
        files = [
            FileTreeDiffManifestFile(path=path, main_content_hash=file["main_content_hash"])
            for path, file in data["files"].items()
        ]
        return cls(files)

    def as_dict(self) -> dict:
        return asdict(self)


class FileTreeDiffFileStatus(StrEnum):
    """Status of a file in the file tree diff."""

    added = auto()
    deleted = auto()
    modified = auto()

    @property
    def emoji(self) -> str:
        """Return an emoji representing the file status."""
        if self == FileTreeDiffFileStatus.added:
            return "➕"
        elif self == FileTreeDiffFileStatus.deleted:
            return "➖"
        elif self == FileTreeDiffFileStatus.modified:
            return "📝"
        return ""


class FileTreeDiffFile:
    def __init__(
        self,
        path: str,
        status: FileTreeDiffFileStatus,
        diff: "FileTreeDiff",
    ):
        self.path = path
        self.status = status
        self.current_version = diff.current_version
        self.current_version_build = diff.current_version_build
        self.base_version = diff.base_version
        self.base_version_build = diff.base_version_build
        self._resolver = diff._resolver

    @property
    def url(self):
        """URL to the file in the current version."""
        return self._resolver.resolve_version(
            project=self.current_version.project,
            version=self.current_version,
            filename=self.path,
        )

    @property
    def base_url(self):
        """URL to the file in the base version."""
        return self._resolver.resolve_version(
            project=self.base_version.project,
            version=self.base_version,
            filename=self.path,
        )


class FileTreeDiff:
    """Difference between two file tree manifests."""

    def __init__(
        self,
        current_version: Version,
        current_version_build: Build,
        base_version: Version,
        base_version_build: Build,
        files: list[tuple[str, FileTreeDiffFileStatus]],
    ):
        self.project = current_version.project
        self.current_version = current_version
        self.current_version_build = current_version_build
        self.base_version = base_version
        self.base_version_build = base_version_build
        self._resolver = Resolver()
        # Per-build manifests make the diff fully reproducible from the builds
        # themselves, so there is no "outdated" state. Kept for template
        # backwards compatibility.
        self.outdated = False
        self.files = sorted(
            (
                FileTreeDiffFile(path=path, status=status, diff=self)
                for path, status in self._filter_files(files)
            ),
            key=self._sortpath,
        )

    def _filter_files(
        self, files: list[tuple[str, FileTreeDiffFileStatus]]
    ) -> Iterator[tuple[str, FileTreeDiffFileStatus]]:
        ignore_patterns = self.project.addons.filetreediff_ignored_files or []
        return (
            (path, status)
            for path, status in files
            if not any(fnmatch.fnmatch(path, ignore_pattern) for ignore_pattern in ignore_patterns)
        )

    def _sortpath(self, file: FileTreeDiffFile):
        """
        Function to use as `key=` argument for `sorted`.

        It sorts the file names by the less deep directories first.
        However, it doesn't group the results by directory.

        Ideally, this should sort file names by hierarchy (less deep directory
        first), grouping them by directory and alphabetically. We should update
        this function to achieve that goal if we find a simple way to do it.
        """
        parts = file.path.split("/")
        return len(parts), parts

    @cached_property
    def added(self):
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.added]

    @cached_property
    def deleted(self):
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.deleted]

    @cached_property
    def modified(self):
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.modified]

    @cached_property
    def should_auto_expand(self):
        """Auto-expand the details view when there are few files."""
        return len(self.files) < 5
