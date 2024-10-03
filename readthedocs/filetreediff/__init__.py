import json
from dataclasses import dataclass

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Version
from readthedocs.projects.constants import MEDIA_TYPE_METADATA
from readthedocs.storage import build_media_storage


@dataclass
class FileTreeDiff:
    added: list[str]
    removed: list[str]
    modified: list[str]


def get_diff(version_a: Version, version_b: Version) -> FileTreeDiff | None:
    version_a_manifest = get_manifest(version_a)
    version_b_manifest = get_manifest(version_b)

    if not version_a_manifest or not version_b_manifest:
        return None

    files_a = set(version_a_manifest.get("files", {}).keys())
    files_b = set(version_b_manifest.get("files", {}).keys())

    files_added = list(files_a - files_b)
    files_removed = list(files_b - files_a)
    files_modified = []
    for file_path in files_a & files_b:
        file_a = version_a_manifest["files"][file_path]
        file_b = version_b_manifest["files"][file_path]

        if file_a["hash"] != file_b["hash"]:
            files_modified.append(file_path)

    return FileTreeDiff(
        added=files_added,
        removed=files_removed,
        modified=files_modified,
    )


def get_manifest(version: Version):
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_METADATA,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, "manifest.json")
    try:
        with build_media_storage.open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)
    except FileNotFoundError:
        return None

    latest_successful_build = version.builds.filter(
        state=BUILD_STATE_FINISHED,
        success=True,
    ).first()
    if not latest_successful_build:
        return None

    build_id_from_manifest = manifest.get("build", {}).get("id")
    if latest_successful_build.id != build_id_from_manifest:
        # The manifest is outdated,
        # do we want to still use it? do we care?
        # Should the caller be responsible to handle this?
        return None

    return manifest


def write_manifest(version: Version, manifest: dict):
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_METADATA,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, "manifest.json")
    with build_media_storage.open(manifest_path, "w") as f:
        json.dump(manifest, f)
