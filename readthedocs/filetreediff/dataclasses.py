from dataclasses import asdict
from dataclasses import dataclass


@dataclass(slots=True)
class FileTreeDiffBuild:
    """The build associated with a file tree manifest."""

    id: int


@dataclass(slots=True)
class FileTreeDiffFile:
    """A file in a file tree manifest."""

    path: str
    main_content_hash: str


@dataclass(slots=True)
class FileTreeDiffManifest:
    """A list of files and the build associated with them."""

    files: dict[str, FileTreeDiffFile]
    build: FileTreeDiffBuild

    def __init__(self, build_id: int, files: list[FileTreeDiffFile]):
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
            FileTreeDiffFile(path=path, main_content_hash=file["main_content_hash"])
            for path, file in data["files"].items()
        ]
        return cls(build_id, files)

    def as_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return asdict(self)


@dataclass
class FileTreeDiff:
    """Difference between two file tree manifests."""

    added: list[str]
    deleted: list[str]
    modified: list[str]
    outdated: bool = False

    def has_changes(self) -> bool:
        return bool(self.added or self.deleted or self.modified)
