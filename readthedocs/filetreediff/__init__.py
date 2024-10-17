import json
from dataclasses import asdict, dataclass

from readthedocs.builds.models import Version
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.storage import build_media_storage

MANIFEST_FILE_NAME = "manifest.json"


@dataclass(slots=True)
class FileTreeBuild:
    id: int


@dataclass(slots=True)
class FileTreeFile:
    path: str
    main_content_hash: str


@dataclass(slots=True)
class FileTreeManifest:
    files: dict[str, FileTreeFile]
    build: FileTreeBuild

    def __init__(self, build_id: int, files: list[FileTreeFile]):
        self.build = FileTreeBuild(id=build_id)
        self.files = {file.path: file for file in files}

    @classmethod
    def from_dict(cls, data: dict) -> "FileTreeManifest":
        build_id = data["build"]["id"]
        files = [
            FileTreeFile(path=path, main_content_hash=file["main_content_hash"])
            for path, file in data["files"].items()
        ]
        return cls(build_id, files)


@dataclass
class FileTreeDiff:
    added: list[str]
    deleted: list[str]
    modified: list[str]
    outdated: bool = False


def get_diff(version_a: Version, version_b: Version) -> FileTreeDiff | None:
    outdated = False
    manifests: list[FileTreeManifest] = []
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

    return FileTreeDiff(
        added=files_added,
        deleted=files_deleted,
        modified=files_modified,
        outdated=outdated,
    )


def get_manifest(version: Version) -> FileTreeManifest | None:
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

    return FileTreeManifest.from_dict(manifest)


def write_manifest(version: Version, manifest: FileTreeManifest):
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_DIFF,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, MANIFEST_FILE_NAME)
    with build_media_storage.open(manifest_path, "w") as f:
        json.dump(asdict(manifest), f)
