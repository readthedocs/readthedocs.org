from dataclasses import dataclass


@dataclass(slots=True)
class FileTreeBuild:

    """The build associated with a file tree manifest."""

    id: int


@dataclass(slots=True)
class FileTreeFile:

    """A file in a file tree manifest."""

    path: str
    main_content_hash: str


@dataclass(slots=True)
class FileTreeManifest:

    """A list of files and the build associated with them."""

    files: dict[str, FileTreeFile]
    build: FileTreeBuild

    def __init__(self, build_id: int, files: list[FileTreeFile]):
        self.build = FileTreeBuild(id=build_id)
        self.files = {file.path: file for file in files}

    @classmethod
    def from_dict(cls, data: dict) -> "FileTreeManifest":
        """
        Create a FileTreeManifest from a dictionary.

        The dictionary should follow the same structure as the one returned by
        converting the object to a dictionary using the `asdict` function.
        """
        build_id = data["build"]["id"]
        files = [
            FileTreeFile(path=path, main_content_hash=file["main_content_hash"])
            for path, file in data["files"].items()
        ]
        return cls(build_id, files)


@dataclass
class FileTreeDiff:

    """Difference between two file tree manifests."""

    added: list[str]
    deleted: list[str]
    modified: list[str]
    outdated: bool = False

    def has_changes(self) -> bool:
        return bool(self.added or self.deleted or self.modified)
