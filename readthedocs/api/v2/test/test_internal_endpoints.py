"""
Internal-only endpoints must reject the API keys we expose to users.

``HasInternalAPIKey`` is the only thing keeping builder-only data (plaintext
environment variables, build state, storage credentials) away from project
API keys, since both share the same model. These tests pin that down.
"""

from django.test import TestCase
from django_dynamic_fixture import get
from rest_framework.test import APIClient

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import EnvironmentVariable
from readthedocs.projects.models import Project


class InternalEndpointsTests(TestCase):
    def setUp(self):
        self.project = get(Project, privacy_level=PUBLIC)
        self.version = get(Version, project=self.project, privacy_level=PUBLIC)
        self.build = get(Build, project=self.project, version=self.version)
        get(
            EnvironmentVariable,
            project=self.project,
            name="SECRET",
            value="hunter2",
            public=False,
        )

        _, self.internal_key = BuildAPIKey.objects.create_internal_key(self.project)
        self.project_api_key, self.project_key = BuildAPIKey.objects.create_project_key(
            project=self.project,
            name="user key",
            permission_level=BuildAPIKey.PermissionLevel.READ_WRITE,
        )
        self.client = APIClient()

    def _authenticate(self, key):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

    def test_project_detail_hides_environment_variables_from_project_keys(self):
        url = f"/api/v2/project/{self.project.pk}/"

        # Positive control: the builders do get the values.
        self._authenticate(self.internal_key)
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data["environment_variables"]["SECRET"]["value"] == "hunter2"

        # A project key only gets the public serializer.
        self._authenticate(self.project_key)
        response = self.client.get(url)
        assert response.status_code == 200
        assert "environment_variables" not in response.data

    def test_internal_only_endpoints_reject_project_keys(self):
        self._authenticate(self.project_key)

        response = self.client.get(
            "/api/v2/build/concurrent/",
            {"project__slug": self.project.slug},
        )
        assert response.status_code == 403

        response = self.client.post(f"/api/v2/build/{self.build.pk}/reset/")
        assert response.status_code == 403

        response = self.client.post(
            f"/api/v2/build/{self.build.pk}/credentials/storage/",
            {"type": "build_media"},
        )
        assert response.status_code == 403

        response = self.client.post(
            "/api/v2/command/",
            {"build": self.build.pk, "command": "true", "output": "", "exit_code": 0},
        )
        assert response.status_code == 403

        response = self.client.post(
            "/api/v2/notifications/",
            {"attached_to": f"build/{self.build.pk}", "message_id": "build:cancelled-by-user"},
        )
        assert response.status_code == 403

    def test_build_state_cannot_be_modified_with_project_keys(self):
        self._authenticate(self.project_key)

        response = self.client.patch(f"/api/v2/build/{self.build.pk}/", {"success": True})
        assert response.status_code == 403

        response = self.client.patch(f"/api/v2/version/{self.version.pk}/", {"built": True})
        assert response.status_code == 403

        response = self.client.patch(f"/api/v2/project/{self.project.pk}/", {"name": "pwned"})
        assert response.status_code == 403

    def test_revoke_endpoint_rejects_project_keys(self):
        self._authenticate(self.project_key)
        response = self.client.post("/api/v2/revoke/")
        assert response.status_code == 403

        self.project_api_key.refresh_from_db()
        assert self.project_api_key.revoked is False
