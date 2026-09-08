from datetime import timedelta

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.projects.models import Project


class ProjectAPIKeyViewsTests(TestCase):
    def setUp(self):
        self.user = fixture.get(User, username="owner")
        self.user.set_password("test")
        self.user.save()
        self.project = fixture.get(Project, slug="pip", users=[self.user])

        self.other_user = fixture.get(User, username="other")
        self.other_user.set_password("test")
        self.other_user.save()

        self.list_url = reverse("projects_apikeys", args=[self.project.slug])
        self.create_url = reverse("projects_apikeys_create", args=[self.project.slug])

        self.client.force_login(self.user)

    def _revoke_url(self, api_key):
        return reverse("projects_apikeys_revoke", args=[self.project.slug, api_key.pk])

    def test_list_is_empty_by_default(self):
        response = self.client.get(self.list_url)
        assert response.status_code == 200
        assert list(response.context["object_list"]) == []

    def test_create_key(self):
        response = self.client.post(
            self.create_url,
            data={
                "name": "my key",
                "expires_in": "30",
                "permission_level": BuildAPIKey.PermissionLevel.READ_WRITE,
                "description": "used by CI",
            },
        )
        self.assertRedirects(response, self.list_url)

        api_key = BuildAPIKey.objects.get(project=self.project)
        assert api_key.name == "my key"
        assert api_key.description == "used by CI"
        assert api_key.permission_level == BuildAPIKey.PermissionLevel.READ_WRITE
        assert api_key.expiry_date is not None
        expected = timezone.now() + timedelta(days=30)
        assert abs((api_key.expiry_date - expected).total_seconds()) < 60

    def test_create_key_without_expiration(self):
        self.client.post(
            self.create_url,
            data={
                "name": "my key",
                "expires_in": "never",
                "permission_level": BuildAPIKey.PermissionLevel.READ_ONLY,
            },
        )
        api_key = BuildAPIKey.objects.get(project=self.project)
        assert api_key.expiry_date is None

    def test_key_is_shown_only_once(self):
        self.client.post(
            self.create_url,
            data={
                "name": "my key",
                "expires_in": "30",
                "permission_level": BuildAPIKey.PermissionLevel.READ_ONLY,
            },
        )

        response = self.client.get(self.list_url)
        key = response.context["created_api_key"]
        assert key
        assert BuildAPIKey.objects.get_from_key(key).project == self.project

        response = self.client.get(self.list_url)
        assert response.context["created_api_key"] is None

    def test_revoke_key(self):
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=self.project, name="my key"
        )
        response = self.client.post(self._revoke_url(api_key))
        self.assertRedirects(response, self.list_url)

        api_key.refresh_from_db()
        assert api_key.revoked is True
        # The key is kept around for the audit trail, but hidden from the list.
        assert list(self.client.get(self.list_url).context["object_list"]) == []

    def test_revoke_requires_post(self):
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=self.project, name="my key"
        )
        response = self.client.get(self._revoke_url(api_key))
        assert response.status_code == 405

    def test_non_admin_cannot_access_the_views(self):
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=self.project, name="my key"
        )
        self.client.force_login(self.other_user)

        assert self.client.get(self.list_url).status_code == 404
        assert self.client.get(self.create_url).status_code == 404
        assert self.client.post(self._revoke_url(api_key)).status_code == 404

        api_key.refresh_from_db()
        assert api_key.revoked is False

    def test_internal_keys_are_hidden(self):
        internal_key, _ = BuildAPIKey.objects.create_internal_key(self.project)
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=self.project, name="my key"
        )

        response = self.client.get(self.list_url)
        assert list(response.context["object_list"]) == [api_key]

        # Builder keys can't be revoked from the dashboard either.
        response = self.client.post(self._revoke_url(internal_key))
        assert response.status_code == 404
        internal_key.refresh_from_db()
        assert internal_key.revoked is False

    def test_key_from_another_project_cannot_be_revoked(self):
        others_project = fixture.get(Project, slug="others", users=[self.user])
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=others_project, name="my key"
        )
        response = self.client.post(self._revoke_url(api_key))
        assert response.status_code == 404

        api_key.refresh_from_db()
        assert api_key.revoked is False
