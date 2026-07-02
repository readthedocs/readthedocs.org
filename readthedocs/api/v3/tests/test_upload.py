import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.constants import (
    BRANCH,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
)
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


@override_settings(
    RTD_BUILD_MEDIA_STORAGE="readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest",
    RTD_BUILD_UPLOADS_STORAGE="readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest",
    RTD_ALLOW_ORGANIZATIONS=False,
)
class UploadAPITests(TestCase):
    def setUp(self):
        self.user = fixture.get(User, username="uploaduser")
        self.token = fixture.get(Token, user=self.user)
        self.project = fixture.get(
            Project,
            slug="test-project",
            name="Test Project",
            users=[self.user],
            versions=[],
            related_projects=[],
            main_language_project=None,
            privacy_level=PUBLIC,
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_upload_initiate_creates_build_and_version(self):
        """Test that initiate creates a build and version."""
        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "project": self.project.slug,
                "version": {
                    "name": "main",
                    "type": "branch",
                    "commit": "abc123def456",
                },
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        data = response.json()

        # Check response structure
        assert "build" in data
        assert "version" in data
        assert "upload_url" in data

        # Check build was created
        build = Build.objects.get(pk=data["build"]["id"])
        assert build.is_uploaded is True
        assert build.state == BUILD_STATE_TRIGGERED
        assert build.commit == "abc123def456"
        assert build.project == self.project

        # Check version was created
        version = Version.objects.get(pk=data["version"]["id"])
        assert version.verbose_name == "main"
        assert version.type == BRANCH
        assert version.project == self.project

    def test_upload_initiate_reuses_existing_version(self):
        """Test that initiate reuses an existing version."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="develop",
            slug="develop",
            type=BRANCH,
            active=True,
        )

        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "project": self.project.slug,
                "version": {
                    "name": "develop",
                    "type": "branch",
                    "commit": "deadbeef",
                },
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()

        # Should reuse the existing version
        assert data["version"]["id"] == version.id

    def test_upload_initiate_requires_project(self):
        """Test that project slug is required."""
        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "version": {
                    "name": "main",
                    "type": "branch",
                    "commit": "abc123",
                },
            },
            format="json",
        )
        assert response.status_code == 400

    def test_upload_initiate_requires_admin(self):
        """Test that non-admin users can't initiate uploads."""
        other_user = fixture.get(User, username="otheruser")
        other_token = fixture.get(Token, user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "project": self.project.slug,
                "version": {
                    "name": "main",
                    "type": "branch",
                    "commit": "abc123",
                },
            },
            format="json",
        )
        assert response.status_code == 404

    def test_upload_initiate_cancels_existing_builds(self):
        """Test that initiating an upload cancels existing in-progress builds."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        existing_build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
        )

        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "project": self.project.slug,
                "version": {
                    "name": "main",
                    "type": "branch",
                    "commit": "newcommit",
                },
            },
            format="json",
        )
        assert response.status_code == 201

        # Existing build should be cancelled
        existing_build.refresh_from_db()
        assert existing_build.state == BUILD_STATE_CANCELLED

    def test_upload_initiate_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        self.client.credentials()  # Remove auth
        response = self.client.post(
            "/api/v3/upload/initiate/",
            data={
                "project": self.project.slug,
                "version": {
                    "name": "main",
                    "type": "branch",
                    "commit": "abc123",
                },
            },
            format="json",
        )
        assert response.status_code == 401

    def test_upload_complete_success(self):
        """Test completing an upload triggers processing."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
            success=True,
        )

        response = self.client.post(
            "/api/v3/upload/complete/",
            data={
                "build": build.id,
                "status": "uploaded",
            },
            format="json",
        )
        assert response.status_code == 202
        assert "build" in response.json()

    def test_upload_complete_failure(self):
        """Test marking an upload as failed."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
            success=True,
        )

        response = self.client.post(
            "/api/v3/upload/complete/",
            data={
                "build": build.id,
                "status": "failed",
            },
            format="json",
        )
        assert response.status_code == 200

        build.refresh_from_db()
        assert build.state == BUILD_STATE_FINISHED
        assert build.success is False

    def test_upload_complete_non_uploaded_build(self):
        """Test that non-uploaded builds can't be completed via this endpoint."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=False,
        )

        response = self.client.post(
            "/api/v3/upload/complete/",
            data={
                "build": build.id,
                "status": "uploaded",
            },
            format="json",
        )
        assert response.status_code == 404

    def test_upload_complete_already_finished_build(self):
        """Test that finished builds return conflict."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_FINISHED,
            is_uploaded=True,
        )

        response = self.client.post(
            "/api/v3/upload/complete/",
            data={
                "build": build.id,
                "status": "uploaded",
            },
            format="json",
        )
        assert response.status_code == 409

    def test_upload_complete_requires_admin(self):
        """Test that non-admin users can't complete uploads."""
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            slug="main",
            type=BRANCH,
            active=True,
        )
        build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
        )

        other_user = fixture.get(User, username="otheruser2")
        other_token = fixture.get(Token, user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        response = self.client.post(
            "/api/v3/upload/complete/",
            data={
                "build": build.id,
                "status": "uploaded",
            },
            format="json",
        )
        assert response.status_code == 403
