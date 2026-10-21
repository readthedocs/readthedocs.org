import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.api.v3.authentication import RTDAPIKeyAuthentication
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

    def test_last_used(self):
        api_key, key = self._create_key()
        assert api_key.last_used_at is None
        modified = api_key.modified

        authentication = RTDAPIKeyAuthentication()
        authentication.authenticate_credentials(key)
        api_key.refresh_from_db()
        last_used_at = api_key.last_used_at
        assert last_used_at is not None
        # The modified date isn't changed when the key is used.
        assert api_key.modified == modified

        authentication.authenticate_credentials(key)
        api_key.refresh_from_db()
        assert api_key.last_used_at > last_used_at

    def test_created_by_is_kept_when_the_user_is_deleted(self):
        user = get(User, username="eric")
        user_id = user.pk
        api_key, _ = self._create_key(created_by=user)
        assert api_key.created_by == user
        assert api_key.created_by_user_id == user_id
        assert api_key.created_by_username == "eric"

        user.delete()
        api_key.refresh_from_db()
        assert api_key.created_by is None
        assert api_key.created_by_user_id == user_id
        assert api_key.created_by_username == "eric"

    def test_created_by_username_isnt_updated(self):
        user = get(User, username="eric")
        api_key, _ = self._create_key(created_by=user)

        user.username = "new-username"
        user.save()
        api_key.name = "new name"
        api_key.save()
        api_key.refresh_from_db()
        assert api_key.created_by_username == "eric"

    def test_created_by_empty(self):
        api_key, _ = self._create_key()
        assert api_key.created_by is None
        assert api_key.created_by_user_id is None
        assert api_key.created_by_username == ""

    def test_revoked_at(self):
        api_key, _ = self._create_key()
        assert api_key.revoked_at is None

        api_key.revoked = True
        api_key.save()
        api_key.refresh_from_db()
        revoked_at = api_key.revoked_at
        assert revoked_at is not None

        # It isn't changed when the key is saved again.
        api_key.name = "new name"
        api_key.save()
        api_key.refresh_from_db()
        assert api_key.revoked_at == revoked_at

    def test_modified_is_updated_on_save(self):
        api_key, _ = self._create_key()
        modified = api_key.modified
        assert modified is not None

        api_key.name = "new name"
        api_key.save()
        api_key.refresh_from_db()
        assert api_key.modified > modified
