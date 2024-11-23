from dataclasses import asdict, dataclass


@dataclass(slots=True)
class FileSection:
    id: str
    title: str


@dataclass(slots=True)
class Page:
    path: str
    sections: list[FileSection]


@dataclass(slots=True)
class FileSectionManifest:
    build: int
    pages: list[Page]

    def __init__(self, build_id: int, pages: list[Page]):
        self.build = build_id
        self.pages = pages

    @classmethod
    def from_dict(cls, data: dict) -> "FileSectionManifest":
        build_id = data["build"]
        pages = [
            Page(
                path=page["path"],
                sections=[FileSection(**section) for section in page["sections"]],
            )
            for page in data["pages"]
        ]
        return cls(build_id, pages)

    def as_dict(self) -> dict:
        return asdict(self)
