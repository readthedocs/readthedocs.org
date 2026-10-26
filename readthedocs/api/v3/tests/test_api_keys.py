import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.api.v3.authentication import RTDTokenAuthentication
from readthedocs.api.v3.models import ProjectPermission
from readthedocs.api.v3.models import RTDToken
from readthedocs.projects.models import Project


class RTDTokenTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="project")

    def _create_key(self, **kwargs):
        return RTDToken.objects.create_key(
            name="key",
            project=self.project,
            permissions=[ProjectPermission.UPLOAD],
            **kwargs,
        )

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_community_key_prefix(self):
        token, key = self._create_key()
        assert token.prefix.startswith("rtdorg_project_")
        assert key.startswith(f"{token.prefix}.")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_business_key_prefix(self):
        token, key = self._create_key()
        assert token.prefix.startswith("rtdcom_project_")
        assert key.startswith(f"{token.prefix}.")

    def test_pk_doesnt_include_the_hashed_key(self):
        token, _ = self._create_key()
        assert isinstance(token.pk, int)
        assert RTDToken.objects.get(pk=token.pk) == token

    def test_fields_fit_max_length(self):
        # SQLite doesn't enforce max_length, check it explicitly.
        token, _ = self._create_key()
        for field in ("prefix", "hashed_key"):
            max_length = RTDToken._meta.get_field(field).max_length
            assert len(getattr(token, field)) <= max_length

    def test_get_from_key(self):
        token, key = self._create_key()
        assert RTDToken.objects.get_from_key(key) == token
        assert token.has_permission(ProjectPermission.UPLOAD)

    def test_get_from_key_without_platform_prefix(self):
        token, key = self._create_key()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_key(key.removeprefix("rtdorg_project_"))

    def test_get_from_key_with_another_platform_prefix(self):
        _, key = self._create_key()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_key(key.replace("rtdorg_", "rtdcom_", 1))

    def test_get_from_key_invalid_secret(self):
        _, key = self._create_key()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_key(key + "x")

    def test_get_from_key_revoked(self):
        token, key = self._create_key()
        token.revoked = True
        token.save()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_key(key)

    def test_key_without_project(self):
        token, key = RTDToken.objects.create_key(
            name="key",
            permissions=[ProjectPermission.UPLOAD],
        )
        assert token.project is None
        assert not token.is_project_scoped
        assert RTDToken.objects.get_from_key(key) == token

    def test_get_permissions_display(self):
        token, _ = self._create_key()
        assert token.get_permissions_display() == ["Upload documentation"]

        # Unknown permissions are skipped.
        token.permissions = [ProjectPermission.UPLOAD, "project:unknown"]
        assert token.get_permissions_display() == ["Upload documentation"]

    def test_last_used(self):
        token, key = self._create_key()
        assert token.last_used_at is None
        modified = token.modified

        authentication = RTDTokenAuthentication()
        authentication.authenticate_credentials(key)
        token.refresh_from_db()
        last_used_at = token.last_used_at
        assert last_used_at is not None
        # The modified date isn't changed when the key is used.
        assert token.modified == modified

        authentication.authenticate_credentials(key)
        token.refresh_from_db()
        assert token.last_used_at > last_used_at

    def test_created_by_is_kept_when_the_user_is_deleted(self):
        user = get(User, username="eric")
        user_id = user.pk
        token, _ = self._create_key(created_by=user)
        assert token.created_by == user
        assert token.created_by_user_id == user_id
        assert token.created_by_username == "eric"

        user.delete()
        token.refresh_from_db()
        assert token.created_by is None
        assert token.created_by_user_id == user_id
        assert token.created_by_username == "eric"

    def test_created_by_username_isnt_updated(self):
        user = get(User, username="eric")
        token, _ = self._create_key(created_by=user)

        user.username = "new-username"
        user.save()
        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.created_by_username == "eric"

    def test_created_by_empty(self):
        token, _ = self._create_key()
        assert token.created_by is None
        assert token.created_by_user_id is None
        assert token.created_by_username == ""

    def test_revoked_at(self):
        token, _ = self._create_key()
        assert token.revoked_at is None

        token.revoked = True
        token.save()
        token.refresh_from_db()
        revoked_at = token.revoked_at
        assert revoked_at is not None

        # It isn't changed when the key is saved again.
        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.revoked_at == revoked_at

    def test_modified_is_updated_on_save(self):
        token, _ = self._create_key()
        modified = token.modified
        assert modified is not None

        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.modified > modified
