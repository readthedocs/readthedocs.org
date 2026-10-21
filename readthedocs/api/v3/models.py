from enum import StrEnum

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.crypto import KeyGenerator
from rest_framework_api_key.crypto import concatenate
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager

from readthedocs.projects.models import Project


class ProjectPermission(models.TextChoices):
    """
    Permissions that can be granted to a project scoped API key.

    Only upload is supported for now, read and write can be added later.
    """

    UPLOAD = "project:upload", _("Upload documentation")


class APIKeyScope(StrEnum):
    """
    Scope that an API key can have.

    Currently only project scoped keys are supported, but organization and user scoped keys
    can be added in the future.
    """

    PROJECT = "project"


def get_platform_prefix():
    """Prefix used to identify the platform (Community or Business) a key belongs to."""
    return "rtdcom" if settings.ALLOW_PRIVATE_REPOS else "rtdorg"


def get_key_prefix(scope):
    """
    Return the prefix used to identify the platform and scope of a key.

    For example, ``rtdorg_project_`` for a project scoped key in Read the Docs Community.
    """
    return f"{get_platform_prefix()}_{scope}_"


class RTDAPIKeyGenerator(KeyGenerator):
    """
    Generate keys prefixed with the platform and scope of the key.

    Keys have the form ``rtdorg_project_<random>.<secret>``.
    The ``rtdorg_project_<random>`` part is stored as the prefix to look up the key,
    the full key is hashed.
    """

    # pylint: disable=arguments-differ
    def generate(self, scope):
        prefix = get_key_prefix(scope) + self.get_prefix()
        secret_key = self.get_secret_key()
        key = concatenate(prefix, secret_key)
        hashed_key = self.hash(key)
        return key, prefix, hashed_key


class RTDAPIKeyManager(BaseAPIKeyManager):
    key_generator = RTDAPIKeyGenerator()

    def assign_key(self, obj):
        key, prefix, hashed_key = self.key_generator.generate(scope=obj.scope)
        obj.prefix = prefix
        obj.hashed_key = hashed_key
        return key

    def get_scope_from_key(self, key):
        """Return the scope of the key from its prefix, or ``None`` if it isn't one of our keys."""
        for scope in APIKeyScope:
            if key.startswith(get_key_prefix(scope)):
                return scope
        return None

    def get_usable_keys(self) -> models.QuerySet:
        """Override to select related project for performance when checking permissions."""
        return super().get_usable_keys().select_related("project")


class RTDAPIKey(AbstractAPIKey):
    """
    API key scoped to a project, with a set of permissions.

    This is the model for all API keys that users can create,
    other scopes (like organization or user) will be added in the future.
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text=_("Project that this API key grants access to"),
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("What this API key is used for"),
    )
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of permissions granted to this API key"),
    )
    modified = models.DateTimeField(_("Modified"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_api_keys",
        help_text=_("User that created this API key"),
    )
    last_used = models.DateTimeField(
        _("Last used"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API key was last used, updated at most once per hour"),
    )
    revoked_at = models.DateTimeField(
        _("Revoked at"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API key was revoked"),
    )

    # The library uses the prefix and the hashed key as the primary key,
    # use an auto-incremented ID instead, so the hashed key isn't exposed in URLs or relations.
    id = models.BigAutoField(primary_key=True)
    # Override to fit the platform and scope part of the prefix (e.g. ``rtdorg_project_``).
    prefix = models.CharField(max_length=32, unique=True, editable=False)

    objects = RTDAPIKeyManager()

    class Meta(AbstractAPIKey.Meta):
        verbose_name = _("API key")
        verbose_name_plural = _("API keys")

    def save(self, *args, **kwargs):
        # Keys can be revoked from the dashboard or the admin, set the date in both cases.
        if self.revoked and not self.revoked_at:
            self.revoked_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def scope(self):
        # TODO: when adding organization and user scoped keys, return the correct scope here.
        return APIKeyScope.PROJECT

    @property
    def is_project_scoped(self):
        return self.scope == APIKeyScope.PROJECT

    def has_permission(self, permission):
        # TODO: when adding read/write permissions, resolve implied permissions here
        # (e.g. write implies read), keep storing only the permissions that were granted.
        return permission in self.permissions

    def get_permissions_display(self):
        """Return the human readable names of the permissions of this key."""
        return [
            ProjectPermission(permission).label
            for permission in self.permissions
            if permission in ProjectPermission.values
        ]
