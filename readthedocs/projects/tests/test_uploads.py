"""Unit tests for the pre-built HTML upload helpers."""

import io
import zipfile

import django_dynamic_fixture as fixture
import pytest

from readthedocs.builds.constants import SOURCE_TYPE_UPLOAD
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.uploads import InvalidUploadArchiveError
from readthedocs.projects.tasks.uploads import validate_archive


def _make_zip(entries):
    """``entries`` is a dict of {arcname: bytes}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    buf.seek(0)
    return buf


@pytest.fixture
def upload_version(db):
    project = fixture.get(Project, slug="proj")
    return fixture.get(
        Version,
        project=project,
        slug="0.3",
        verbose_name="0.3",
        type=TAG,
        source_type=SOURCE_TYPE_UPLOAD,
    )


def test_validate_minimal_archive():
    buf = _make_zip({"html/index.html": b"<html></html>"})
    archive = validate_archive(buf)

    assert archive.size > 0
    assert "html" in archive.top_level_dirs
    assert len(archive.sha256) == 64
    # File pointer must be rewound for the storage save() that follows.
    assert buf.tell() == 0


def test_validate_accepts_optional_formats():
    buf = _make_zip(
        {
            "html/index.html": b"<html></html>",
            "pdf/docs.pdf": b"%PDF-1.4",
            "epub/docs.epub": b"PK",
            "htmlzip/docs.zip": b"PK",
        }
    )
    archive = validate_archive(buf)
    assert archive.top_level_dirs == frozenset({"html", "pdf", "epub", "htmlzip"})


def test_validate_rejects_missing_html():
    buf = _make_zip({"pdf/docs.pdf": b"%PDF-1.4"})
    with pytest.raises(InvalidUploadArchiveError, match="missing required directories"):
        validate_archive(buf)


def test_validate_rejects_unknown_top_level_dir():
    buf = _make_zip(
        {
            "html/index.html": b"<html></html>",
            "src/secret.py": b"print('hi')",
        }
    )
    with pytest.raises(InvalidUploadArchiveError, match="Disallowed top-level entry"):
        validate_archive(buf)


def test_validate_rejects_path_traversal():
    buf = _make_zip({"html/index.html": b"<html></html>", "../etc/passwd": b"x"})
    with pytest.raises(InvalidUploadArchiveError, match="Path traversal"):
        validate_archive(buf)


def test_validate_rejects_absolute_path():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("html/index.html", b"<html></html>")
        # Force an absolute-looking name that bypasses zipfile's normalization.
        info = zipfile.ZipInfo("/etc/passwd")
        zf.writestr(info, b"x")
    buf.seek(0)
    with pytest.raises(InvalidUploadArchiveError, match="Absolute path"):
        validate_archive(buf)


def test_validate_rejects_empty_archive():
    buf = io.BytesIO(b"")
    with pytest.raises(InvalidUploadArchiveError, match="empty"):
        validate_archive(buf)


def test_validate_rejects_non_zip():
    buf = io.BytesIO(b"this is not a zip file at all")
    with pytest.raises(InvalidUploadArchiveError, match="Not a valid zip"):
        validate_archive(buf)


def test_get_upload_storage_path(upload_version):
    upload_version.upload_content_hash = "deadbeef" * 8
    assert upload_version.get_upload_storage_path() == (
        f"uploads/proj/0.3/{'deadbeef' * 8}.zip"
    )


def test_get_upload_storage_path_returns_none_without_hash(upload_version):
    assert upload_version.get_upload_storage_path() is None
