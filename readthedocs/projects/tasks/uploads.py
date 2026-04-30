"""
Helpers for the pre-built HTML upload feature.

A user uploads a ``.zip`` archive via the APIv3 upload endpoint. The web side
validates the archive and stores it on ``build_media_storage`` at::

    uploads/<project_slug>/<version_slug>/<sha256>.zip

The archive must contain only the artifact directories Read the Docs supports
at the top level: ``html/``, ``htmlzip/``, ``pdf/`` and ``epub/``. ``html/``
is required.

At build time, :func:`extract_uploaded_archive` downloads the archive from
storage and unzips it into ``project.artifact_path(<type>)``. From there the
existing ``store_build_artifacts`` flow takes over and copies the artifacts to
their permanent location.
"""

import hashlib
import os
import zipfile
from dataclasses import dataclass

import structlog

from readthedocs.builds.constants import ARTIFACT_TYPES
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)


# Top-level directories accepted inside the uploaded archive. ``html`` is
# required; the rest are optional.
ALLOWED_TOP_LEVEL_DIRS = frozenset(ARTIFACT_TYPES) - {"json"}
REQUIRED_TOP_LEVEL_DIRS = frozenset({"html"})

# Hard caps that match the validation contract documented in the API endpoint.
# Tune via settings if needed; these are the demo defaults.
MAX_UPLOAD_SIZE_BYTES = 1 * 1024 * 1024 * 1024  # 1 GiB compressed
MAX_UNCOMPRESSED_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5 GiB uncompressed
MAX_COMPRESSION_RATIO = 200  # uncompressed / compressed
MAX_FILE_COUNT = 50_000


class InvalidUploadArchiveError(Exception):
    """The uploaded archive failed validation."""


@dataclass
class ValidatedArchive:
    sha256: str
    size: int
    top_level_dirs: frozenset


def validate_archive(file_obj):
    """
    Validate an uploaded zip archive without extracting it.

    Performs three classes of check:

    * **Path safety** — reject absolute paths, ``..`` traversal and symlinks.
    * **Size** — reject archives larger than :data:`MAX_UPLOAD_SIZE_BYTES`,
      whose uncompressed contents exceed :data:`MAX_UNCOMPRESSED_SIZE_BYTES`,
      or whose compression ratio exceeds :data:`MAX_COMPRESSION_RATIO`
      (zip-bomb defense).
    * **Layout** — top-level entries must all be in
      :data:`ALLOWED_TOP_LEVEL_DIRS` and must include ``html/``.

    Returns a :class:`ValidatedArchive` describing the archive on success;
    raises :class:`InvalidUploadArchiveError` otherwise. The file pointer is
    rewound to the start before returning.
    """
    file_obj.seek(0, os.SEEK_END)
    compressed_size = file_obj.tell()
    file_obj.seek(0)

    if compressed_size == 0:
        raise InvalidUploadArchiveError("Uploaded archive is empty.")
    if compressed_size > MAX_UPLOAD_SIZE_BYTES:
        raise InvalidUploadArchiveError(
            f"Uploaded archive is too large ({compressed_size} bytes; "
            f"max {MAX_UPLOAD_SIZE_BYTES})."
        )

    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
        sha256.update(chunk)
    file_obj.seek(0)

    try:
        zf = zipfile.ZipFile(file_obj)
    except zipfile.BadZipFile as exc:
        raise InvalidUploadArchiveError(f"Not a valid zip archive: {exc}") from exc

    infos = zf.infolist()
    if len(infos) > MAX_FILE_COUNT:
        raise InvalidUploadArchiveError(
            f"Archive contains too many files ({len(infos)}; max {MAX_FILE_COUNT})."
        )

    total_uncompressed = 0
    top_level_dirs = set()
    for info in infos:
        _check_member_safe(info)
        total_uncompressed += info.file_size

        first = info.filename.split("/", 1)[0]
        if first and first not in ALLOWED_TOP_LEVEL_DIRS:
            raise InvalidUploadArchiveError(
                f"Disallowed top-level entry {first!r}; "
                f"expected one of {sorted(ALLOWED_TOP_LEVEL_DIRS)}."
            )
        if first:
            top_level_dirs.add(first)

    if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
        raise InvalidUploadArchiveError(
            f"Archive uncompressed size is too large ({total_uncompressed} bytes; "
            f"max {MAX_UNCOMPRESSED_SIZE_BYTES})."
        )
    if compressed_size and total_uncompressed / compressed_size > MAX_COMPRESSION_RATIO:
        raise InvalidUploadArchiveError("Archive compression ratio is suspiciously high.")

    missing = REQUIRED_TOP_LEVEL_DIRS - top_level_dirs
    if missing:
        raise InvalidUploadArchiveError(
            f"Archive is missing required directories: {sorted(missing)}."
        )

    file_obj.seek(0)
    return ValidatedArchive(
        sha256=sha256.hexdigest(),
        size=compressed_size,
        top_level_dirs=frozenset(top_level_dirs),
    )


def _check_member_safe(info):
    name = info.filename
    if name.startswith("/") or os.path.isabs(name):
        raise InvalidUploadArchiveError(f"Absolute path in archive: {name!r}.")
    # Reject any path segment that resolves above the root, even with mixed separators.
    parts = name.replace("\\", "/").split("/")
    if any(part in ("..",) for part in parts):
        raise InvalidUploadArchiveError(f"Path traversal in archive: {name!r}.")
    # Reject symlinks (POSIX mode in the upper 16 bits of external_attr).
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode and (mode & 0xF000) == 0xA000:
        raise InvalidUploadArchiveError(f"Symlink in archive: {name!r}.")


def store_uploaded_archive(version, file_obj, sha256):
    """
    Persist a validated archive to ``build_media_storage`` and return the key.

    The caller is responsible for invoking :func:`validate_archive` first and
    passing the resulting hash. Older archives at the same key are overwritten.
    """
    key = version.get_upload_storage_path(content_hash=sha256)
    file_obj.seek(0)
    if build_media_storage.exists(key):
        build_media_storage.delete(key)
    build_media_storage.save(key, file_obj)
    return key


def extract_uploaded_archive(version, destination_dir, storage=None):
    """
    Download the archive for ``version`` and extract it into ``destination_dir``.

    ``destination_dir`` is the ``_readthedocs/`` directory of the build (the
    parent of ``html/``, ``pdf/`` etc.) — the contents of the zip are written
    there directly.

    Returns the set of top-level directories actually extracted, so the caller
    can update flags such as ``Version.has_pdf``.
    """
    storage = storage or build_media_storage
    key = version.get_upload_storage_path()
    if not key:
        raise InvalidUploadArchiveError(
            f"Version {version.slug!r} has no uploaded archive to extract."
        )

    os.makedirs(destination_dir, exist_ok=True)
    extracted = set()
    with storage.open(key, "rb") as remote:
        # ZipFile needs a seekable file-like. Storage backends typically return
        # one; if not, the caller can stage to a tempfile first.
        with zipfile.ZipFile(remote) as zf:
            for info in zf.infolist():
                _check_member_safe(info)
                first = info.filename.split("/", 1)[0]
                if first and first in ALLOWED_TOP_LEVEL_DIRS:
                    extracted.add(first)
            zf.extractall(destination_dir)
    log.info(
        "Extracted uploaded archive.",
        version_slug=version.slug,
        project_slug=version.project.slug,
        key=key,
        top_level_dirs=sorted(extracted),
    )
    return frozenset(extracted)
