from datetime import timedelta

import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.api.v2.models import BuildAPIKey

from .mixins import APIEndpointMixin


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    PRODUCTION_DOMAIN="readthedocs.org",
    RTD_ALLOW_ORGANIZATIONS=False,
)
class ProjectAPIKeyEndpointTests(APIEndpointMixin):
    def setUp(self):
        super().setUp()
        self.api_key, self.key = BuildAPIKey.objects.create_project_key(
            project=self.project,
            name="test key",
            permission_level=BuildAPIKey.PermissionLevel.READ_WRITE,
        )
        self.readonly_api_key, self.readonly_key = BuildAPIKey.objects.create_project_key(
            project=self.project,
            name="read only key",
            permission_level=BuildAPIKey.PermissionLevel.READ_ONLY,
        )

    def _authenticate(self, key):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

    def test_projects_list_only_returns_the_keys_project(self):
        self._authenticate(self.key)
        response = self.client.get(reverse("projects-list"))
        assert response.status_code == 200
        assert [project["slug"] for project in response.json()["results"]] == [
            self.project.slug
        ]

    def test_project_detail(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 200
        assert response.json()["slug"] == self.project.slug

    def test_other_project_is_not_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-detail", kwargs={"project_slug": self.others_project.slug}
            )
        )
        assert response.status_code == 404

    def test_versions_list(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-versions-list",
                kwargs={"parent_lookup_project__slug": self.project.slug},
            )
        )
        assert response.status_code == 200
        assert response.json()["count"] > 0

    def test_other_project_versions_are_not_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-versions-list",
                kwargs={"parent_lookup_project__slug": self.others_project.slug},
            )
        )
        assert response.status_code == 401

    def test_read_write_key_can_update_a_version(self):
        self._authenticate(self.key)
        assert self.version.active is True
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data={"active": False},
        )
        assert response.status_code == 204
        self.version.refresh_from_db()
        assert self.version.active is False

    def test_read_only_key_can_read(self):
        self._authenticate(self.readonly_key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 200

    def test_read_only_key_cannot_write(self):
        self._authenticate(self.readonly_key)
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data={"active": False},
        )
        assert response.status_code == 401
        self.version.refresh_from_db()
        assert self.version.active is True

    def test_environment_variables_are_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-environmentvariables-list",
                kwargs={"parent_lookup_project__slug": self.project.slug},
            )
        )
        assert response.status_code == 200

    def test_read_write_key_can_create_an_environment_variable(self):
        self._authenticate(self.key)
        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={"parent_lookup_project__slug": self.project.slug},
            ),
            data={"name": "TEST", "value": "value", "public": False},
        )
        assert response.status_code == 201
        assert self.project.environmentvariable_set.filter(name="TEST").exists()

    def test_builds_are_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-builds-list",
                kwargs={"parent_lookup_project__slug": self.project.slug},
            )
        )
        assert response.status_code == 200

    def test_project_notifications_are_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-notifications-list",
                kwargs={"parent_lookup_project__slug": self.project.slug},
            )
        )
        assert response.status_code == 200

    def test_build_notifications_are_reachable(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "projects-builds-notifications-list",
                kwargs={
                    "parent_lookup_build__id": self.build.pk,
                    "parent_lookup_project__slug": self.project.slug,
                },
            )
        )
        assert response.status_code == 200

    def test_user_endpoints_are_denied(self):
        self._authenticate(self.key)
        response = self.client.get(
            reverse(
                "users-notifications-list",
                kwargs={"parent_lookup_user__username": self.me.username},
            )
        )
        assert response.status_code == 401

    def test_creating_a_project_is_denied(self):
        self._authenticate(self.key)
        response = self.client.post(
            reverse("projects-list"),
            data={
                "name": "new project",
                "repository": {"url": "https://github.com/rtfd/new", "type": "git"},
                "homepage": "http://example.com",
                "programming_language": "py",
                "language": "en",
            },
        )
        assert response.status_code == 401

    def test_expired_key_is_denied(self):
        self.api_key.expiry_date = timezone.now() - timedelta(days=1)
        self.api_key.save()
        self._authenticate(self.key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 401

    def test_key_without_expiration_never_expires(self):
        assert self.api_key.expiry_date is None
        assert self.api_key.has_expired is False

    def test_revoked_key_is_denied(self):
        self.api_key.revoked = True
        self.api_key.save()
        self._authenticate(self.key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 401

    def test_user_token_still_works(self):
        self._authenticate(self.token.key)
        response = self.client.get(reverse("projects-list"))
        assert response.status_code == 200

    def test_invalid_user_token_is_rejected(self):
        self._authenticate("invalidtoken")
        response = self.client.get(reverse("projects-list"))
        assert response.status_code == 401

    def test_build_api_key_is_rejected(self):
        _, build_key = BuildAPIKey.objects.create_internal_key(project=self.project)
        self._authenticate(build_key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 401

    def test_key_from_another_project_cannot_access_this_one(self):
        _, other_key = BuildAPIKey.objects.create_project_key(
            project=self.others_project,
            name="other key",
            permission_level=BuildAPIKey.PermissionLevel.READ_WRITE,
        )
        self._authenticate(other_key)
        response = self.client.get(
            reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        )
        assert response.status_code == 404

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_RATES": {"anon": "1/minute", "user": "60/minute"},
            "TEST_REQUEST_DEFAULT_FORMAT": "json",
        }
    )
    def test_anonymous_throttle_does_not_apply_to_api_keys(self):
        self._authenticate(self.key)
        url = reverse("projects-detail", kwargs={"project_slug": self.project.slug})
        assert self.client.get(url).status_code == 200
        assert self.client.get(url).status_code == 200


class ProjectAPIKeyModelTests(APIEndpointMixin):
    def test_create_key_returns_a_usable_key(self):
        api_key, key = BuildAPIKey.objects.create_project_key(
            project=self.project, name="test key"
        )
        assert BuildAPIKey.objects.get_from_key(key) == api_key
        assert api_key.is_read_only is True

    def test_name_is_trimmed_to_the_max_length(self):
        _, key = BuildAPIKey.objects.create_project_key(project=self.project, name="a" * 60)
        assert BuildAPIKey.objects.get_from_key(key).name == "a" * 50

    def test_revoked_key_cannot_be_retrieved(self):
        api_key, key = BuildAPIKey.objects.create_project_key(
            project=self.project, name="test key"
        )
        api_key.revoked = True
        api_key.save()
        with self.assertRaises(BuildAPIKey.DoesNotExist):
            BuildAPIKey.objects.get_from_key(key)

    def test_expiry_date_is_stored(self):
        expiry_date = timezone.now() + timedelta(days=30)
        api_key, _ = BuildAPIKey.objects.create_project_key(
            project=self.project, name="test key", expiry_date=expiry_date
        )
        assert api_key.expiry_date == expiry_date
        assert api_key.has_expired is False
