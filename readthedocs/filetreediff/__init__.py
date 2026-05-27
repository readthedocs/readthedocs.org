"""
File tree diff (FTD) — show which files changed in a documentation build.

Each successful build writes a manifest of ``{path: main_content_hash}`` to a
per-build path in storage. A diff between two builds is a set comparison of
those manifests.

Storage path layout::

    diff/{project}/{version}/builds/{build_id}/manifest.json

Pinning the base for pull request builds is done with the
``Build.diff_base_build`` self-FK: when the first build of a pull request
version runs, its FK is set to the base version's latest successful build at
that moment. Subsequent PR builds inherit the same pin from the prior PR
build. This keeps the diff stable as the base branch moves forward.

Normal version builds compare against the most recent successful build of
the same version (no pinning needed).
"""

import json

import structlog

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.filetreediff.dataclasses import FileTreeDiff
from readthedocs.filetreediff.dataclasses import FileTreeDiffFileStatus
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifestFile
from readthedocs.projects.constants import MEDIA_TYPE_DIFF
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)


def _manifest_path(build: Build) -> str:
    return build.version.get_storage_path(
        media_type=MEDIA_TYPE_DIFF,
        filename=f"builds/{build.id}/manifest.json",
    )


def get_manifest_for_build(build: Build) -> FileTreeDiffManifest | None:
    """Read the manifest for a single build, or None if it isn't written."""
    try:
        with build_media_storage.open(_manifest_path(build)) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    return FileTreeDiffManifest.from_dict(data)


def write_manifest(build: Build, file_hashes: dict[str, str]):
    """Write the manifest for a build at its per-build path."""
    manifest = FileTreeDiffManifest(
        files=[
            FileTreeDiffManifestFile(path=path, main_content_hash=content_hash)
            for path, content_hash in file_hashes.items()
        ],
    )
    with build_media_storage.open(_manifest_path(build), "w") as f:
        json.dump(manifest.as_dict(), f)


def delete_manifest_for_build(build: Build):
    """Best-effort delete of a build's manifest when its Build row is pruned."""
    if not build.version_id:
        return
    try:
        build_media_storage.delete(_manifest_path(build))
    except Exception:
        log.exception(
            "Failed to delete build manifest from storage.",
            build_id=build.id,
        )


def resolve_pr_diff_base_build(version, build) -> Build | None:
    """
    Pick the base build to pin a pull-request build's diff against.

    Inherits the pin from the most recent prior PR build of the same version
    so subsequent builds stay anchored to the same base. Falls back to the
    base version's current latest successful build for the very first PR
    build.
    """
    prior = (
        version.builds.filter(
            state=BUILD_STATE_FINISHED,
            success=True,
            id__lt=build.id,
            diff_base_build__isnull=False,
        )
        .order_by("-id")
        .only("diff_base_build_id")
        .first()
    )
    if prior:
        return prior.diff_base_build

    project = version.project
    base_version = project.addons.options_base_version or project.get_latest_version()
    if not base_version:
        return None
    return base_version.latest_successful_build


def _resolve_base_build_for_diff(build: Build) -> Build | None:
    """Pick the base build to diff against for an already-completed build."""
    version = build.version
    if not version:
        return None

    if version.is_external:
        return build.diff_base_build

    return (
        version.builds.filter(
            state=BUILD_STATE_FINISHED,
            success=True,
            id__lt=build.id,
        )
        .order_by("-id")
        .first()
    )


def get_diff_for_build(build: Build) -> FileTreeDiff | None:
    """
    Compute the file tree diff for a build against the correct base.

    Returns ``None`` when the build didn't finish successfully, when no base
    build can be resolved (first build of a version, or PR pin not set), or
    when either manifest is missing from storage.
    """
    if not build.success or build.state != BUILD_STATE_FINISHED:
        return None
    if not build.version_id:
        return None

    base_build = _resolve_base_build_for_diff(build)
    if not base_build:
        return None

    current_manifest = get_manifest_for_build(build)
    if not current_manifest:
        return None

    base_manifest = get_manifest_for_build(base_build)
    if not base_manifest:
        return None

    current_paths = set(current_manifest.files.keys())
    base_paths = set(base_manifest.files.keys())

    files: list[tuple[str, FileTreeDiffFileStatus]] = []
    for path in current_paths - base_paths:
        files.append((path, FileTreeDiffFileStatus.added))
    for path in base_paths - current_paths:
        files.append((path, FileTreeDiffFileStatus.deleted))
    for path in current_paths & base_paths:
        current_hash = current_manifest.files[path].main_content_hash
        base_hash = base_manifest.files[path].main_content_hash
        if current_hash != base_hash:
            files.append((path, FileTreeDiffFileStatus.modified))

    return FileTreeDiff(
        current_version=build.version,
        current_version_build=build,
        base_version=base_build.version,
        base_version_build=base_build,
        files=files,
    )
