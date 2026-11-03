from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.api.v3.authentication import RTDTokenAuthentication
from readthedocs.api.v3.models import ProjectPermission
from readthedocs.api.v3.models import RTDToken
from readthedocs.projects.models import Project


class RTDTokenTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="project")

    def _create_token(self, **kwargs):
        return RTDToken.objects.create_token(
            name="token",
            project=self.project,
            permissions=[ProjectPermission.UPLOAD],
            **kwargs,
        )

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_community_token_prefix(self):
        token, plain_token = self._create_token()
        assert token.prefix.startswith("rtdorg_project_")
        assert plain_token.startswith(f"{token.prefix}_")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_business_token_prefix(self):
        token, plain_token = self._create_token()
        assert token.prefix.startswith("rtdcom_project_")
        assert plain_token.startswith(f"{token.prefix}_")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_token_format(self):
        token, plain_token = self._create_token()
        platform, scope, random, secret = plain_token.split("_")
        assert platform == "rtdorg"
        assert scope == "project"
        assert token.prefix == f"{platform}_{scope}_{random}"
        assert len(secret) == 32

    def test_get_from_token_with_dot_separator(self):
        token, plain_token = self._create_token()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(f"{token.prefix}.{plain_token.rpartition('_')[2]}")

    def test_pk_doesnt_include_the_hashed_token(self):
        token, _ = self._create_token()
        assert isinstance(token.pk, int)
        assert RTDToken.objects.get(pk=token.pk) == token

    def test_fields_fit_max_length(self):
        # SQLite doesn't enforce max_length, check it explicitly.
        token, _ = self._create_token()
        for field in ("prefix", "hashed_token"):
            max_length = RTDToken._meta.get_field(field).max_length
            assert len(getattr(token, field)) <= max_length

    def test_get_from_token(self):
        token, plain_token = self._create_token()
        assert RTDToken.objects.get_from_token(plain_token) == token
        assert token.has_permission(ProjectPermission.UPLOAD)

    def test_get_from_token_without_platform_prefix(self):
        token, plain_token = self._create_token()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token.removeprefix("rtdorg_project_"))

    def test_get_from_token_with_another_platform_prefix(self):
        _, plain_token = self._create_token()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token.replace("rtdorg_", "rtdcom_", 1))

    def test_get_from_token_invalid_secret(self):
        _, plain_token = self._create_token()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token + "x")

    def test_get_from_token_revoked(self):
        token, plain_token = self._create_token()
        token.revoke()
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token)

    def test_token_without_project(self):
        token, plain_token = RTDToken.objects.create_token(
            name="token",
            permissions=[ProjectPermission.UPLOAD],
        )
        assert token.project is None
        assert not token.is_project_scoped
        assert RTDToken.objects.get_from_token(plain_token) == token

    def test_get_permissions_display(self):
        token, _ = self._create_token()
        assert token.get_permissions_display() == ["Upload documentation"]

        # Unknown permissions are skipped.
        token.permissions = [ProjectPermission.UPLOAD, "project:unknown"]
        assert token.get_permissions_display() == ["Upload documentation"]

    def test_last_used(self):
        token, plain_token = self._create_token()
        assert token.last_used_at is None
        modified = token.modified

        authentication = RTDTokenAuthentication()
        authentication.authenticate_credentials(plain_token)
        token.refresh_from_db()
        last_used_at = token.last_used_at
        assert last_used_at is not None
        # The modified date isn't changed when the token is used.
        assert token.modified == modified

        authentication.authenticate_credentials(plain_token)
        token.refresh_from_db()
        assert token.last_used_at > last_used_at

    def test_update_last_used(self):
        token, _ = self._create_token()
        modified = token.modified

        token.update_last_used()
        last_used_at = token.last_used_at
        assert last_used_at is not None
        token.refresh_from_db()
        assert token.last_used_at == last_used_at
        assert token.modified == modified

    def test_update_last_used_only_moves_forward(self):
        token, _ = self._create_token()
        # Another request set a later date.
        later = timezone.now() + timedelta(minutes=5)
        RTDToken.objects.filter(pk=token.pk).update(last_used_at=later)

        token.update_last_used()
        assert token.last_used_at == later
        token.refresh_from_db()
        assert token.last_used_at == later

    def test_created_by_is_kept_when_the_user_is_deleted(self):
        user = get(User, username="eric")
        user_id = user.pk
        token, _ = self._create_token(created_by=user)
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
        token, _ = self._create_token(created_by=user)

        user.username = "new-username"
        user.save()
        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.created_by_username == "eric"

    def test_created_by_empty(self):
        token, _ = self._create_token()
        assert token.created_by is None
        assert token.created_by_user_id is None
        assert token.created_by_username == ""

    def test_revoked_at(self):
        token, _ = self._create_token()
        assert token.revoked_at is None

        token.revoke()
        token.refresh_from_db()
        revoked_at = token.revoked_at
        assert revoked_at is not None

        # It isn't changed when the token is saved again.
        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.revoked_at == revoked_at

    def test_saving_a_stale_instance_doesnt_restore_a_revoked_token(self):
        token, plain_token = self._create_token()
        # Loaded before the token is revoked, e.g. by an admin editing it.
        stale_token = RTDToken.objects.get(pk=token.pk)

        RTDToken.objects.get(pk=token.pk).revoke()
        stale_token.name = "new name"
        stale_token.save()

        token.refresh_from_db()
        assert token.is_revoked
        assert token.name == "new name"
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token)

    def test_saving_a_stale_instance_doesnt_overwrite_last_used_at(self):
        token, plain_token = self._create_token()
        stale_token = RTDToken.objects.get(pk=token.pk)

        RTDTokenAuthentication().authenticate_credentials(plain_token)
        stale_token.name = "new name"
        stale_token.save()

        token.refresh_from_db()
        assert token.last_used_at is not None

    def test_revoking_a_stale_instance_keeps_the_original_date(self):
        token, _ = self._create_token()
        stale_token = RTDToken.objects.get(pk=token.pk)

        token.revoke()
        revoked_at = token.revoked_at
        stale_token.revoke()

        assert stale_token.revoked_at == revoked_at
        token.refresh_from_db()
        assert token.revoked_at == revoked_at

    def test_revoked_token_cant_be_restored(self):
        token, _ = self._create_token()
        token.revoke()

        token.revoked_at = None
        with pytest.raises(ValidationError):
            token.full_clean()
        with pytest.raises(ValidationError):
            token.save()

        token = RTDToken.objects.get(pk=token.pk)
        token.revoked_at = None
        with pytest.raises(ValidationError):
            token.save()
        token.refresh_from_db()
        assert token.is_revoked

    def test_outdated_hash_is_updated(self):
        token, plain_token = self._create_token()
        token.hashed_token = make_password(plain_token)
        token.save()
        assert not token.hashed_token.startswith("sha512$$")
        modified = token.modified

        assert RTDToken.objects.get_from_token(plain_token) == token
        token.refresh_from_db()
        assert token.hashed_token.startswith("sha512$$")
        assert token.modified == modified
        assert RTDToken.objects.get_from_token(plain_token) == token

    def test_outdated_hash_isnt_updated_with_an_invalid_token(self):
        token, plain_token = self._create_token()
        hashed_token = make_password(plain_token)
        token.hashed_token = hashed_token
        token.save()

        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token + "x")
        token.refresh_from_db()
        assert token.hashed_token == hashed_token

    def test_modified_is_updated_on_save(self):
        token, _ = self._create_token()
        modified = token.modified
        assert modified is not None

        token.name = "new name"
        token.save()
        token.refresh_from_db()
        assert token.modified > modified

    def test_create_from_admin(self):
        admin_user = get(User, is_staff=True, is_superuser=True)
        self.client.force_login(admin_user)
        response = self.client.post(
            reverse("admin:v3_rtdtoken_add"),
            {
                "name": "admin token",
                "project": self.project.pk,
                "description": "",
                "permissions": '["project:upload"]',
            },
            follow=True,
        )
        assert response.status_code == 200
        token = RTDToken.objects.get(name="admin token")
        assert token.created_by == admin_user

        # The token is shown once in a message.
        [message] = [str(m) for m in response.context["messages"] if " is: " in str(m)]
        plain_token = message.split(" is: ")[1].split(". ")[0]
        assert RTDToken.objects.get_from_token(plain_token) == token

    def test_invalid_permissions(self):
        for permissions in [
            {ProjectPermission.UPLOAD: False},
            True,
            ProjectPermission.UPLOAD,
            [1],
            [],
            ["project:unknown"],
        ]:
            with pytest.raises(ValidationError):
                RTDToken.objects.create_token(
                    name="token",
                    project=self.project,
                    permissions=permissions,
                )

            token = RTDToken(name="token", project=self.project, permissions=permissions)
            with pytest.raises(ValidationError) as exc:
                token.full_clean(exclude=["prefix", "hashed_token"])
            assert "permissions" in exc.value.message_dict
        assert not RTDToken.objects.exists()

    def test_invalid_permissions_from_admin(self):
        admin_user = get(User, is_staff=True, is_superuser=True)
        self.client.force_login(admin_user)
        response = self.client.post(
            reverse("admin:v3_rtdtoken_add"),
            {
                "name": "admin token",
                "project": self.project.pk,
                "description": "",
                "permissions": '{"project:upload": false}',
            },
        )
        assert response.status_code == 200
        assert "permissions" in response.context["adminform"].form.errors
        assert not RTDToken.objects.exists()

    def test_revoke_from_admin(self):
        admin_user = get(User, is_staff=True, is_superuser=True)
        self.client.force_login(admin_user)
        token, plain_token = self._create_token()
        self.client.post(
            reverse("admin:v3_rtdtoken_changelist"),
            {"action": "revoke", "_selected_action": [token.pk]},
        )
        token.refresh_from_db()
        assert token.is_revoked
        with pytest.raises(RTDToken.DoesNotExist):
            RTDToken.objects.get_from_token(plain_token)
