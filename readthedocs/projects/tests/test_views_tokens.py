from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.api.v3.models import ProjectPermission
from readthedocs.api.v3.models import RTDAPIKey
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project


class ProjectTokenViewsTests(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="project", users=[self.user])
        self.feature = get(
            Feature,
            feature_id=Feature.ALLOW_DIRECT_ARTIFACTS_UPLOAD,
            projects=[self.project],
        )
        self.client.force_login(self.user)
        self.list_url = reverse("projects_tokens", args=[self.project.slug])
        self.create_url = reverse("projects_tokens_create", args=[self.project.slug])

    def _create_key(self, **kwargs):
        return RTDAPIKey.objects.create_key(
            name="key",
            project=self.project,
            permissions=[ProjectPermission.UPLOAD],
            **kwargs,
        )

    def test_create(self):
        response = self.client.post(
            self.create_url,
            {
                "name": "CI",
                "description": "Upload from GitHub Actions",
                "permissions": [ProjectPermission.UPLOAD],
                "expires_in": "30",
            },
        )
        assert response.status_code == 302
        assert response["Location"] == self.list_url

        api_key = RTDAPIKey.objects.get(project=self.project)
        assert api_key.name == "CI"
        assert api_key.description == "Upload from GitHub Actions"
        assert api_key.permissions == [ProjectPermission.UPLOAD]
        assert api_key.expiry_date.date() == (timezone.now() + timedelta(days=30)).date()

        # The key is shown once.
        response = self.client.get(self.list_url)
        key = response.context["created_token"]
        assert RTDAPIKey.objects.get_from_key(key) == api_key
        response = self.client.get(self.list_url)
        assert response.context["created_token"] is None

    def test_create_without_expiration(self):
        response = self.client.post(
            self.create_url,
            {
                "name": "CI",
                "permissions": [ProjectPermission.UPLOAD],
                "expires_in": "never",
            },
        )
        assert response.status_code == 302
        api_key = RTDAPIKey.objects.get(project=self.project)
        assert api_key.expiry_date is None

    def test_create_with_custom_expiration(self):
        expiration_date = timezone.now().date() + timedelta(days=10)
        response = self.client.post(
            self.create_url,
            {
                "name": "CI",
                "permissions": [ProjectPermission.UPLOAD],
                "expires_in": "custom",
                "expiration_date": expiration_date.isoformat(),
            },
        )
        assert response.status_code == 302
        api_key = RTDAPIKey.objects.get(project=self.project)
        assert api_key.expiry_date.date() == expiration_date
        assert api_key.expiry_date > timezone.now() + timedelta(days=10)

    def test_create_with_custom_expiration_requires_a_date(self):
        response = self.client.post(
            self.create_url,
            {
                "name": "CI",
                "permissions": [ProjectPermission.UPLOAD],
                "expires_in": "custom",
            },
        )
        assert response.status_code == 200
        assert "expiration_date" in response.context["form"].errors
        assert not RTDAPIKey.objects.exists()

    def test_create_with_custom_expiration_today(self):
        response = self.client.post(
            self.create_url,
            {
                "name": "CI",
                "permissions": [ProjectPermission.UPLOAD],
                "expires_in": "custom",
                "expiration_date": timezone.now().date().isoformat(),
            },
        )
        assert response.status_code == 200
        assert "expiration_date" in response.context["form"].errors
        assert not RTDAPIKey.objects.exists()

    def test_create_requires_a_permission(self):
        response = self.client.post(
            self.create_url,
            {"name": "CI", "permissions": [], "expires_in": "30"},
        )
        assert response.status_code == 200
        assert "permissions" in response.context["form"].errors
        assert not RTDAPIKey.objects.exists()

    def test_list_excludes_revoked_keys(self):
        api_key, _ = self._create_key()
        self._create_key(revoked=True)
        response = self.client.get(self.list_url)
        assert list(response.context["object_list"]) == [api_key]

    def test_revoke(self):
        api_key, _ = self._create_key()
        response = self.client.post(
            reverse("projects_tokens_delete", args=[self.project.slug, api_key.prefix]),
        )
        assert response.status_code == 302
        api_key.refresh_from_db()
        assert api_key.revoked

    def test_revoke_key_from_another_project(self):
        other_project = get(Project, slug="other", users=[self.user])
        api_key, _ = RTDAPIKey.objects.create_key(name="key", project=other_project)
        response = self.client.post(
            reverse("projects_tokens_delete", args=[self.project.slug, api_key.prefix]),
        )
        assert response.status_code == 404
        api_key.refresh_from_db()
        assert not api_key.revoked

    def test_feature_flag_required(self):
        self.feature.projects.remove(self.project)
        assert self.client.get(self.list_url).status_code == 404
        assert self.client.get(self.create_url).status_code == 404

    def test_non_admin_user(self):
        self.client.force_login(get(User))
        assert self.client.get(self.list_url).status_code == 404

    def test_sidebar_link(self):
        edit_url = reverse("projects_edit", args=[self.project.slug])
        assert not self.project.is_direct_upload
        response = self.client.get(edit_url)
        assert self.list_url in response.content.decode()

        self.feature.projects.remove(self.project)
        response = self.client.get(edit_url)
        assert self.list_url not in response.content.decode()
