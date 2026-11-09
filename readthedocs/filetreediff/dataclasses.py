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
class FileTreeDiffBuild:
    """The build associated with a file tree manifest."""

    id: int


@dataclass(slots=True)
class FileTreeDiffManifestFile:
    """
    A file in a file tree manifest.

    ``text_hash`` is a hash of the text of the file, ``markup_hash`` a hash of
    its HTML, both taken once the irrelevant nodes are stripped from it (see
    ``readthedocs.search.parsers``). Comparing both tells a page whose copy
    changed from one that only moved its markup around, which isn't used yet:
    see https://github.com/readthedocs/readthedocs.org/issues/13258

    ``main_content_hash`` is a hash of the HTML before stripping anything. It
    is all that manifests written before the other two have, and goes away with
    them (see the ``TODO`` in ``get_diff()``).
    """

    path: str
    main_content_hash: str
    text_hash: str | None = None
    markup_hash: str | None = None


@dataclass(slots=True)
class FileTreeDiffManifest:
    """A list of files and the build associated with them."""

    files: dict[str, FileTreeDiffManifestFile]
    build: FileTreeDiffBuild

    def __init__(self, build_id: int, files: list[FileTreeDiffManifestFile]):
        self.build = FileTreeDiffBuild(id=build_id)
        self.files = {file.path: file for file in files}

    @classmethod
    def from_dict(cls, data: dict) -> "FileTreeDiffManifest":
        """
        Create a FileTreeManifest from a dictionary.

        The dictionary should follow the same structure as the one returned by
        converting the object to a dictionary using the `as_dict` method.
        """
        build_id = data["build"]["id"]
        files = [
            FileTreeDiffManifestFile(
                path=path,
                main_content_hash=file["main_content_hash"],
                text_hash=file.get("text_hash"),
                markup_hash=file.get("markup_hash"),
            )
            for path, file in data["files"].items()
        ]
        return cls(build_id, files)

    def as_dict(self) -> dict:
        """Convert the object to a dictionary."""
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

    @property
    def redirect_from_url(self):
        """
        The path readers request for this file, for a page redirect's ``from_url``.

        Redirects match the requested path, and readers reach ``foo/index.html``
        as ``/foo/`` — which is every page of a MkDocs or ``dirhtml`` build — so
        the ``index.html`` is dropped.
        """
        path = f"/{self.path}"
        if path.endswith("/index.html"):
            path = path[: -len("index.html")]
        return path

    @property
    def diff_url(self):
        """
        URL to the file in the current version with Visual diff switched on.

        ``None`` when the project has the Visual diff addon disabled, since the
        parameter would then do nothing.
        """
        if not self.current_version.project.addons.doc_diff_enabled:
            return None
        return f"{self.url}?readthedocs-diff=true"


class FileTreeDiff:
    """Difference between two file tree manifests."""

    def __init__(
        self,
        current_version: Version,
        current_version_build: Build,
        base_version: Version,
        base_version_build: Build,
        files: list[tuple[str, FileTreeDiffFileStatus]],
        outdated: bool,
    ):
        self.project = current_version.project
        self.current_version = current_version
        self.current_version_build = current_version_build
        self.base_version = base_version
        self.base_version_build = base_version_build
        self._resolver = Resolver()
        self.outdated = outdated
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
        """List of added files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.added]

    @cached_property
    def deleted(self):
        """List of deleted files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.deleted]

    @cached_property
    def modified(self):
        """List of modified files."""
        return [file for file in self.files if file.status == FileTreeDiffFileStatus.modified]

    @cached_property
    def summary(self):
        """Breakdown of the changed files, e.g. ``2 added · 8 modified · 1 deleted``."""
        parts = []
        for label, files in (
            ("added", self.added),
            ("modified", self.modified),
            ("deleted", self.deleted),
        ):
            if files:
                parts.append(f"{len(files)} {label}")
        return " · ".join(parts)

    @cached_property
    def single_status(self):
        """The one status every file shares (``added``, ``modified`` or ``deleted``), or ``None`` when mixed."""
        statuses = {file.status for file in self.files}
        if len(statuses) == 1:
            return statuses.pop().value
        return None

    @cached_property
    def headline(self):
        """
        One line that says how much changed and of what kind.

        ``3 files changed · 1 added · 1 modified · 1 deleted``, or when every file
        is the same kind, just ``25 files deleted``.
        """
        count = len(self.files)
        noun = "file" if count == 1 else "files"
        if self.single_status:
            return f"{count} {noun} {self.single_status}"
        return f"{count} {noun} changed · {self.summary}"

    @cached_property
    def should_collapse(self):
        """
        Whether the comment should fold the file list behind a toggle.

        Ten lines is about what a pull request timeline absorbs before the comment
        dominates it. A handful of edited pages is the whole review and belongs in
        view; forty pages touched by a theme change is a sweep, and the count says
        enough on its own.
        """
        return len(self.files) > 10
