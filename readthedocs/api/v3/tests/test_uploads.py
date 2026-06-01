"""Tests for the APIv3 pre-built HTML upload endpoint."""

import io
import zipfile
from unittest import mock

import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse

from readthedocs.builds.constants import SOURCE_TYPE_UPLOAD
from readthedocs.builds.constants import SOURCE_TYPE_VCS
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC

from .mixins import APIEndpointMixin


def _make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    buf.seek(0)
    return buf


@override_settings(ALLOW_PRIVATE_REPOS=False)
class UploadEndpointTests(APIEndpointMixin):
    def setUp(self):
        super().setUp()
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.upload_version = fixture.get(
            Version,
            project=self.project,
            slug="0.3",
            verbose_name="0.3",
            type=TAG,
            source_type=SOURCE_TYPE_UPLOAD,
            active=True,
            privacy_level=PUBLIC,
        )
        self.url = reverse(
            "projects-versions-upload",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "version_slug": self.upload_version.slug,
            },
        )

    def _post(self, archive, name="docs.zip"):
        archive.seek(0)
        return self.client.post(
            self.url,
            {"file": (name, archive, "application/zip")},
            format="multipart",
        )

    @mock.patch("readthedocs.api.v3.views.trigger_build")
    @mock.patch("readthedocs.api.v3.views.store_uploaded_archive")
    def test_upload_triggers_build_and_persists_hash(self, store_mock, trigger_mock):
        build = fixture.get(Build, project=self.project, version=self.upload_version)
        trigger_mock.return_value = (None, build)
        archive = _make_zip({"html/index.html": b"<html></html>"})

        response = self._post(archive)

        assert response.status_code == 202
        body = response.json()
        assert body["triggered"] is True
        assert body["upload"]["top_level_dirs"] == ["html"]
        assert len(body["upload"]["sha256"]) == 64

        store_mock.assert_called_once()
        trigger_mock.assert_called_once_with(
            project=self.project,
            version=self.upload_version,
        )

        self.upload_version.refresh_from_db()
        assert self.upload_version.upload_content_hash == body["upload"]["sha256"]

    def test_upload_rejects_non_upload_versions(self):
        self.upload_version.source_type = SOURCE_TYPE_VCS
        self.upload_version.save()

        archive = _make_zip({"html/index.html": b"<html></html>"})
        response = self._post(archive)

        assert response.status_code == 400
        assert "source_type" in response.json()

    def test_upload_rejects_invalid_archive(self):
        archive = _make_zip({"src/secret.py": b"print('hi')"})
        response = self._post(archive)

        assert response.status_code == 400
        assert "file" in response.json()

    def test_upload_requires_authentication(self):
        self.client.logout()
        archive = _make_zip({"html/index.html": b"<html></html>"})
        response = self._post(archive)
        assert response.status_code in (401, 403)

    def test_upload_forbidden_for_other_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        archive = _make_zip({"html/index.html": b"<html></html>"})
        response = self._post(archive)
        assert response.status_code in (403, 404)
