"""
Module for the file sections feature.

This feature is used to store the title and path name of each page in the index.
"""

import json
import logging

from readthedocs.builds.models import Version
from readthedocs.filesections.dataclasses import FileSectionManifest
from readthedocs.projects.constants import MEDIA_TYPE_SECTIONS
from readthedocs.storage import build_media_storage

SECTION_MANIFEST_FILE_NAME = "sections_manifest.json"

log = logging.getLogger(__name__)


def get_section_manifest(version: Version) -> FileSectionManifest | None:
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_SECTIONS,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, SECTION_MANIFEST_FILE_NAME)
    try:
        with build_media_storage.open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)
            log.info(f"Loaded section manifest from {manifest_path}")
    except FileNotFoundError:
        log.warning(f"Section manifest not found at {manifest_path}")
        return None

    return FileSectionManifest.from_dict(manifest)


def write_section_manifest(version: Version, manifest: FileSectionManifest):
    storage_path = version.project.get_storage_path(
        type_=MEDIA_TYPE_SECTIONS,
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    manifest_path = build_media_storage.join(storage_path, SECTION_MANIFEST_FILE_NAME)
    with build_media_storage.open(manifest_path, "w") as f:
        manifest_dict = manifest.as_dict()
        log.info(f"Writing section manifest: {manifest_dict}")
        json.dump(manifest_dict, f)
