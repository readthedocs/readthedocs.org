import pytest
from django.test import TestCase
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.api.v3.models import ProjectPermission
from readthedocs.api.v3.models import RTDAPIKey
from readthedocs.projects.models import Project


class RTDAPIKeyTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="project")

    def _create_key(self, **kwargs):
        return RTDAPIKey.objects.create_key(
            name="key",
            project=self.project,
            permissions=[ProjectPermission.UPLOAD],
            **kwargs,
        )

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_community_key_prefix(self):
        api_key, key = self._create_key()
        assert api_key.prefix.startswith("rtdorg_project_")
        assert key.startswith(f"{api_key.prefix}.")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_business_key_prefix(self):
        api_key, key = self._create_key()
        assert api_key.prefix.startswith("rtdcom_project_")
        assert key.startswith(f"{api_key.prefix}.")

    def test_pk_doesnt_include_the_hashed_key(self):
        api_key, _ = self._create_key()
        assert isinstance(api_key.pk, int)
        assert RTDAPIKey.objects.get(pk=api_key.pk) == api_key

    def test_fields_fit_max_length(self):
        # SQLite doesn't enforce max_length, check it explicitly.
        api_key, _ = self._create_key()
        for field in ("prefix", "hashed_key"):
            max_length = RTDAPIKey._meta.get_field(field).max_length
            assert len(getattr(api_key, field)) <= max_length

    def test_get_from_key(self):
        api_key, key = self._create_key()
        assert RTDAPIKey.objects.get_from_key(key) == api_key
        assert api_key.has_permission(ProjectPermission.UPLOAD)

    def test_get_from_key_without_platform_prefix(self):
        api_key, key = self._create_key()
        with pytest.raises(RTDAPIKey.DoesNotExist):
            RTDAPIKey.objects.get_from_key(key.removeprefix("rtdorg_project_"))

    def test_get_from_key_with_another_platform_prefix(self):
        _, key = self._create_key()
        with pytest.raises(RTDAPIKey.DoesNotExist):
            RTDAPIKey.objects.get_from_key(key.replace("rtdorg_", "rtdcom_", 1))

    def test_get_from_key_invalid_secret(self):
        _, key = self._create_key()
        with pytest.raises(RTDAPIKey.DoesNotExist):
            RTDAPIKey.objects.get_from_key(key + "x")

    def test_get_from_key_revoked(self):
        api_key, key = self._create_key()
        api_key.revoked = True
        api_key.save()
        with pytest.raises(RTDAPIKey.DoesNotExist):
            RTDAPIKey.objects.get_from_key(key)

    def test_get_permissions_display(self):
        api_key, _ = self._create_key()
        assert api_key.get_permissions_display() == ["Upload documentation"]

        # Unknown permissions are skipped.
        api_key.permissions = [ProjectPermission.UPLOAD, "project:unknown"]
        assert api_key.get_permissions_display() == ["Upload documentation"]
