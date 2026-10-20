from enum import StrEnum

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.crypto import KeyGenerator
from rest_framework_api_key.crypto import concatenate
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager

from readthedocs.projects.models import Project


class ProjectPermission(StrEnum):
    """
    Permissions that can be granted to a project scoped API key.

    Only upload is supported for now, read and write will be added later.
    """

    UPLOAD = "project:upload"


class APIKeyScope(StrEnum):
    PROJECT = "proj"


def get_platform_prefix():
    """Prefix used to identify the platform (Community or Business) a key belongs to."""
    return "rtdcom" if settings.RTD_ALLOW_ORGANIZATIONS else "rtdorg"


def get_key_prefix(scope):
    """
    Return the prefix used to identify the platform and scope of a key.

    For example, ``rtdorg_proj_`` for a project scoped key in Read the Docs Community.
    """
    return f"{get_platform_prefix()}_{scope}_"


class RTDAPIKeyGenerator(KeyGenerator):
    """
    Generate keys prefixed with the platform and scope of the key.

    Keys have the form ``rtdorg_proj_<prefix>.<secret>``.
    Only the random ``<prefix>`` is stored in the database to look up the key,
    the full key is hashed.
    """

    # pylint: disable=arguments-differ
    def generate(self, scope):
        prefix = self.get_prefix()
        secret_key = self.get_secret_key()
        key = get_key_prefix(scope) + concatenate(prefix, secret_key)
        hashed_key = self.hash(key)
        return key, prefix, hashed_key


class RTDAPIKeyManager(BaseAPIKeyManager):
    key_generator = RTDAPIKeyGenerator()

    def assign_key(self, obj):
        key, prefix, hashed_key = self.key_generator.generate(scope=obj.scope)
        obj.id = concatenate(prefix, hashed_key)
        obj.prefix = prefix
        obj.hashed_key = hashed_key
        return key

    def get_scope_from_key(self, key):
        """Return the scope of the key from its prefix, or ``None`` if it isn't one of our keys."""
        for scope in APIKeyScope:
            if key.startswith(get_key_prefix(scope)):
                return scope
        return None

    def get_from_key(self, key):
        scope = self.get_scope_from_key(key)
        if not scope:
            raise self.model.DoesNotExist("Key is not valid.")

        prefix, _, _ = key.removeprefix(get_key_prefix(scope)).partition(".")
        api_key = self.get_usable_keys().get(prefix=prefix)
        if api_key.scope != scope or not api_key.is_valid(key):
            raise self.model.DoesNotExist("Key is not valid.")
        return api_key


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
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of permissions granted to this API key"),
    )

    objects = RTDAPIKeyManager()

    class Meta(AbstractAPIKey.Meta):
        verbose_name = _("API key")
        verbose_name_plural = _("API keys")

    @property
    def scope(self):
        return APIKeyScope.PROJECT

    def has_permission(self, permission):
        return permission in self.permissions
