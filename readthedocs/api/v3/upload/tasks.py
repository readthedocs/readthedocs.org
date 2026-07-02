"""Task to process uploaded build artifacts."""

import os
import stat
import tempfile
import zipfile

import structlog
from django.core.files.storage import storages

from readthedocs.builds.constants import (
    ARTIFACT_TYPES,
    ARTIFACT_TYPES_WITHOUT_MULTIPLE_FILES_SUPPORT,
    BUILD_STATE_BUILDING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_UPLOADING,
)
from readthedocs.builds.models import Build
from readthedocs.worker import app

log = structlog.get_logger(__name__)

# Validation constants
MAX_UNCOMPRESSED_SIZE = 5 * 1024**3  # 5 GB
MAX_FILES = 50_000
MAX_COMPRESSION_RATIO = 100


@app.task(queue="build:default")
def process_uploaded_build(build_id):
    """
    Process an uploaded build artifact.

    Downloads the zip file from the upload storage, validates it,
    extracts the artifacts, and uploads them to the build media storage.
    """
    try:
        build = Build.objects.get(pk=build_id)
    except Build.DoesNotExist:
        log.error("Build not found for processing.", build_id=build_id)
        return

    structlog.contextvars.bind_contextvars(
        build_id=build.id,
        project_slug=build.project.slug,
        version_slug=build.version.slug if build.version else None,
    )

    log.info("Processing uploaded build.")

    # Update state to building/processing
    build.state = BUILD_STATE_BUILDING
    build.save()

    try:
        upload_key = f"{build.project.id}/{build.id}/artifacts.zip"
        _process_artifacts(build, upload_key)

        # Mark build as successful
        build.state = BUILD_STATE_FINISHED
        build.success = True
        build.save()

        # Mark version as built
        if build.version:
            build.version.built = True
            build.version.save()

        log.info("Upload processing completed successfully.")

    except Exception as e:
        log.exception("Upload processing failed.", error=str(e))
        build.state = BUILD_STATE_FINISHED
        build.success = False
        build.save()


def _process_artifacts(build, upload_key):
    """Download, validate, and store the uploaded artifacts."""
    upload_storage = storages["build-uploads"]
    media_storage = storages["build-media"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "artifacts.zip")

        # Download the zip file from upload storage
        log.info("Downloading artifacts zip.", key=upload_key)
        with upload_storage.open(upload_key, "rb") as source:
            with open(zip_path, "wb") as dest:
                for chunk in source.chunks():
                    dest.write(chunk)

        # Validate the zip file
        log.info("Validating artifacts zip.")
        _validate_zip(zip_path)

        # Extract the zip file
        extract_dir = os.path.join(tmp_dir, "extracted")
        os.makedirs(extract_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # Upload artifacts to final storage
        log.info("Uploading artifacts to media storage.")
        build.state = BUILD_STATE_UPLOADING
        build.save()

        version = build.version
        _upload_artifacts(
            extract_dir=extract_dir,
            version=version,
            media_storage=media_storage,
        )


def _validate_zip(zip_path):
    """
    Validate the uploaded zip file for security and size constraints.

    Checks for:
    - Zip bomb (compression ratio)
    - Path traversal
    - Symlinks
    - Maximum file count and size
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        total_uncompressed = 0
        total_compressed = 0

        for info in zf.infolist():
            # Check for symlinks
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Zip contains symlink: {info.filename}")

            # Check for path traversal
            norm = os.path.normpath(info.filename)
            if norm.startswith(("/", "..")) or os.path.isabs(info.filename):
                raise ValueError(f"Zip contains path traversal: {info.filename}")

            total_uncompressed += info.file_size
            total_compressed += info.compress_size

        # Check total size
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
            raise ValueError(
                f"Zip uncompressed size ({total_uncompressed}) exceeds "
                f"maximum ({MAX_UNCOMPRESSED_SIZE})."
            )

        # Check file count
        if len(zf.infolist()) > MAX_FILES:
            raise ValueError(
                f"Zip contains too many files ({len(zf.infolist())}) "
                f"exceeds maximum ({MAX_FILES})."
            )

        # Check compression ratio (zip bomb detection)
        if (
            total_compressed > 0
            and total_uncompressed / total_compressed > MAX_COMPRESSION_RATIO
        ):
            raise ValueError(
                f"Suspicious compression ratio: "
                f"{total_uncompressed / total_compressed:.1f}x."
            )


def _upload_artifacts(extract_dir, version, media_storage):
    """
    Upload extracted artifacts to their final storage location.

    Expected zip structure:
    - html/       -> HTML documentation
    - pdf/        -> PDF file
    - epub/       -> ePub file
    - htmlzip/    -> HTML zip file
    """
    for artifact_type in ARTIFACT_TYPES:
        artifact_dir = os.path.join(extract_dir, artifact_type)
        if not os.path.isdir(artifact_dir):
            continue

        storage_path = version.get_storage_path(media_type=artifact_type)
        log.info(
            "Uploading artifact.",
            artifact_type=artifact_type,
            storage_path=storage_path,
        )

        if artifact_type in ARTIFACT_TYPES_WITHOUT_MULTIPLE_FILES_SUPPORT:
            # For PDF, ePub, htmlzip: upload the single file
            files = os.listdir(artifact_dir)
            if len(files) == 1:
                file_path = os.path.join(artifact_dir, files[0])
                dest_path = os.path.join(storage_path, files[0])
                with open(file_path, "rb") as f:
                    media_storage.save(dest_path, f)
        else:
            # For HTML/JSON: sync the directory
            if hasattr(media_storage, "rclone_sync_directory"):
                media_storage.rclone_sync_directory(artifact_dir, storage_path)
            else:
                # Fallback: upload files one by one
                for root, _dirs, files in os.walk(artifact_dir):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, artifact_dir)
                        dest_path = os.path.join(storage_path, rel_path)
                        with open(file_path, "rb") as f:
                            media_storage.save(dest_path, f)

        # Update version media flags
        if artifact_type == "pdf":
            version.has_pdf = True
        elif artifact_type == "epub":
            version.has_epub = True
        elif artifact_type == "htmlzip":
            version.has_htmlzip = True

    version.save()
