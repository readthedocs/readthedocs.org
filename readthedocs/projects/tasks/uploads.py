"""
Helpers for the pre-built archive upload feature.

A user uploads a ``.zip`` archive via the APIv3 upload endpoint. The web side
validates the archive and stores it on ``build_media_storage`` at::

    uploads/<project_slug>/<version_slug>/<sha256>.zip

The archive must contain only the artifact directories Read the Docs supports
at the top level: ``html/``, ``htmlzip/``, ``pdf/`` and ``epub/``. ``html/``
is required.

At build time we run ``unzip`` inside the build container — see
``BuildDirector.unzip_uploaded_archive``. The web side never extracts the
archive itself.
"""

import hashlib
import os
import shutil
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


class MissingUploadedArchiveError(Exception):
    """No archive is present on storage for this version (e.g. expired)."""


@dataclass
class ValidatedArchive:
    sha256: str
    size: int
    top_level_dirs: frozenset


def _normalize_name(name):
    """Normalize a zip member name to forward-slash separators."""
    return name.replace("\\", "/")


def _is_ignorable(name):
    """
    Whether a zip member name is junk that we should silently strip.

    Covers the most common user mistakes:

    * macOS resource forks (``__MACOSX/...``) added by ``zip -r`` on macOS.
    * Hidden ``.DS_Store``-style files. They never carry docs content and
      would otherwise blow up the ``BUILD_OUTPUT_HAS_MULTIPLE_FILES`` check
      on offline formats.
    """
    parts = _normalize_name(name).split("/")
    return any(part == "__MACOSX" or part.startswith(".") for part in parts if part)


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
      :data:`ALLOWED_TOP_LEVEL_DIRS` and must include ``html/`` with an
      ``index.html`` inside.

    Error messages never echo entries from the archive — the input is
    untrusted and we don't want to mirror it back into our own logs or
    responses. Returns a :class:`ValidatedArchive` describing the archive on
    success; raises :class:`InvalidUploadArchiveError` otherwise. The file
    pointer is rewound to the start before returning.
    """
    file_obj.seek(0, os.SEEK_END)
    compressed_size = file_obj.tell()
    file_obj.seek(0)

    if compressed_size == 0:
        raise InvalidUploadArchiveError("Uploaded archive is empty.")
    if compressed_size > MAX_UPLOAD_SIZE_BYTES:
        raise InvalidUploadArchiveError(
            f"Uploaded archive is too large (max {MAX_UPLOAD_SIZE_BYTES} bytes)."
        )

    # ``file_digest`` reads in chunks; never loads the whole file into memory.
    sha256 = hashlib.file_digest(file_obj, "sha256").hexdigest()
    file_obj.seek(0)

    try:
        with zipfile.ZipFile(file_obj) as zf:
            archive = _validate_zip_contents(zf, compressed_size)
    except zipfile.BadZipFile as exc:
        raise InvalidUploadArchiveError("Not a valid zip archive.") from exc

    file_obj.seek(0)
    return ValidatedArchive(
        sha256=sha256,
        size=compressed_size,
        top_level_dirs=archive,
    )


def _validate_zip_contents(zf, compressed_size):
    infos = zf.infolist()
    if len(infos) > MAX_FILE_COUNT:
        raise InvalidUploadArchiveError(f"Archive contains too many files (max {MAX_FILE_COUNT}).")

    total_uncompressed = 0
    top_level_dirs = set()
    has_html_index = False
    saw_root_html = False
    for info in infos:
        # Always run the safety check, even for entries we will later ignore,
        # so a traversal hiding inside a junk path (``__MACOSX/../etc``)
        # still rejects the whole archive.
        _check_member_safe(info)
        name = _normalize_name(info.filename)
        if _is_ignorable(name):
            continue
        total_uncompressed += info.file_size

        is_dir_entry = info.is_dir() or name.endswith("/")
        first, _, rest = name.rstrip("/").partition("/")
        if not first:
            continue
        if not rest and not is_dir_entry:
            # File at the archive root. Almost always a user that forgot to
            # wrap their build output in an ``html/`` directory.
            if name.lower().endswith((".html", ".htm")):
                saw_root_html = True
            raise InvalidUploadArchiveError(
                "The archive must put HTML inside an 'html/' directory "
                "(e.g. 'html/index.html'), not at the root."
                if saw_root_html
                else (
                    "Top-level entry not allowed; expected one of "
                    f"{sorted(ALLOWED_TOP_LEVEL_DIRS)}."
                )
            )
        if first not in ALLOWED_TOP_LEVEL_DIRS:
            raise InvalidUploadArchiveError(
                f"Top-level entry not allowed; expected one of {sorted(ALLOWED_TOP_LEVEL_DIRS)}."
            )
        top_level_dirs.add(first)
        if first == "html" and rest == "index.html":
            has_html_index = True

    if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
        raise InvalidUploadArchiveError(
            f"Archive uncompressed size is too large (max {MAX_UNCOMPRESSED_SIZE_BYTES} bytes)."
        )
    if compressed_size and total_uncompressed / compressed_size > MAX_COMPRESSION_RATIO:
        raise InvalidUploadArchiveError("Archive compression ratio is suspiciously high.")

    missing = REQUIRED_TOP_LEVEL_DIRS - top_level_dirs
    if missing:
        raise InvalidUploadArchiveError(
            f"Archive is missing required directories: {sorted(missing)}."
        )
    if "html" in top_level_dirs and not has_html_index:
        raise InvalidUploadArchiveError(
            "Archive is missing 'html/index.html'. The HTML output must "
            "contain an index.html at the root of the html/ directory."
        )

    return frozenset(top_level_dirs)


def _check_member_safe(info):
    """
    Reject path traversal, absolute paths and symlinks.

    Error messages never include the offending name — the archive is
    untrusted input.
    """
    name = _normalize_name(info.filename)
    if name.startswith("/") or os.path.isabs(name):
        raise InvalidUploadArchiveError("Absolute path in archive.")
    if any(part == ".." for part in name.split("/")):
        raise InvalidUploadArchiveError("Path traversal in archive.")
    # Reject symlinks (POSIX mode in the upper 16 bits of external_attr).
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode and (mode & 0xF000) == 0xA000:
        raise InvalidUploadArchiveError("Symlink in archive.")


def store_uploaded_archive(version, file_obj, sha256):
    """
    Persist a validated archive to ``build_media_storage`` and return the key.

    The caller is responsible for invoking :func:`validate_archive` first and
    passing the resulting hash. The key includes the SHA, so when the same
    content is uploaded twice we re-use the existing object instead of
    racing a delete + save.
    """
    key = version.get_upload_storage_path(content_hash=sha256)
    file_obj.seek(0)
    if not build_media_storage.exists(key):
        build_media_storage.save(key, file_obj)
    return key


def stage_uploaded_archive(version, host_path):
    """
    Download the version's archive to a path on the build host.

    The path is expected to live under ``project.checkout_path(version)``,
    which is bind-mounted into the build container. The unzip itself runs
    *inside* that container — see ``BuildDirector.unzip_uploaded_archive`` —
    so the host never executes ``unzip`` directly on user input.
    """
    key = version.get_upload_storage_path()
    if not key:
        raise MissingUploadedArchiveError(
            f"Version {version.slug!r} has no uploaded archive to extract."
        )
    if not build_media_storage.exists(key):
        raise MissingUploadedArchiveError(
            f"Uploaded archive for version {version.slug!r} is no longer available. "
            "Re-upload the archive and trigger a new build."
        )

    os.makedirs(os.path.dirname(host_path), exist_ok=True)
    with build_media_storage.open(key, "rb") as remote, open(host_path, "wb") as local:
        shutil.copyfileobj(remote, local)
    log.info(
        "Staged uploaded archive for build container.",
        version_slug=version.slug,
        project_slug=version.project.slug,
        key=key,
    )
    return host_path
