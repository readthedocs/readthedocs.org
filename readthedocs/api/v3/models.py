from enum import StrEnum

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rest_framework_api_key.crypto import KeyGenerator

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


class RTDTokenGenerator(KeyGenerator):
    """
    Generate keys prefixed with the platform and scope of the key.

    Keys have the form ``rtdorg_project_<random>_<secret>``.
    The ``rtdorg_project_<random>`` part is stored as the prefix to look up the key,
    the full key is hashed.
    The random part and the secret only contain letters and digits,
    so the secret is everything after the last ``_``.
    """

    # pylint: disable=arguments-differ
    def generate(self, scope):
        prefix = get_key_prefix(scope) + self.get_prefix()
        secret_key = self.get_secret_key()
        key = f"{prefix}_{secret_key}"
        hashed_key = self.hash(key)
        return key, prefix, hashed_key

    @staticmethod
    def get_prefix_from_key(key):
        prefix, _, _ = key.rpartition("_")
        return prefix


class RTDTokenManager(models.Manager):
    key_generator = RTDTokenGenerator()

    def assign_key(self, obj):
        """Generate a key for the object, and return the plain key."""
        key, prefix, hashed_key = self.key_generator.generate(scope=obj.scope)
        obj.prefix = prefix
        obj.hashed_key = hashed_key
        return key

    def create_key(self, **kwargs):
        """Create a key, and return a ``(RTDToken, key)`` tuple."""
        obj = self.model(**kwargs)
        key = self.assign_key(obj)
        obj.save()
        return obj, key

    def get_scope_from_key(self, key):
        """Return the scope of the key from its prefix, or ``None`` if it isn't one of our keys."""
        for scope in APIKeyScope:
            if key.startswith(get_key_prefix(scope)):
                return scope
        return None

    def get_usable_keys(self):
        # Select the project for performance when checking permissions.
        return self.filter(revoked_at__isnull=True).select_related("project")

    def get_from_key(self, key):
        """
        Return the key object from the plain key.

        Raises ``DoesNotExist`` if the key doesn't exist, is revoked, or the secret doesn't match.
        Expiration isn't checked here, so callers can give a better error.
        """
        prefix = self.key_generator.get_prefix_from_key(key)
        obj = self.get_usable_keys().get(prefix=prefix)
        if not self.key_generator.verify(key, obj.hashed_key):
            raise self.model.DoesNotExist("Key is not valid.")
        return obj


class RTDToken(TimeStampedModel):
    """
    API key scoped to a project, with a set of permissions.

    This is the model for all API keys that users can create,
    other scopes (like organization or user) will be added in the future.
    """

    # Platform and scope part of the key, plus a random part (e.g. ``rtdorg_project_<random>``),
    # used to look up the key.
    prefix = models.CharField(max_length=32, unique=True, editable=False)
    hashed_key = models.CharField(max_length=150, editable=False)
    name = models.CharField(
        _("Name"),
        max_length=50,
        help_text=_("A name to identify this API key"),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tokens",
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
        help_text=_("List of permissions granted to this API key"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tokens",
        help_text=_("User that created this API key"),
    )
    # Extra information in case the user is deleted.
    created_by_user_id = models.PositiveBigIntegerField(
        _("Created by user ID"),
        null=True,
        blank=True,
        editable=False,
    )
    created_by_username = models.CharField(
        _("Created by username"),
        max_length=150,
        blank=True,
        default="",
        editable=False,
    )
    expires_at = models.DateTimeField(
        _("Expires at"),
        null=True,
        blank=True,
        help_text=_("When the API key expires, it can't be used after this date"),
    )
    last_used_at = models.DateTimeField(
        _("Last used"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API key was last used"),
    )
    # A revoked key can't be used anymore, this can't be undone.
    revoked_at = models.DateTimeField(
        _("Revoked at"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API key was revoked"),
    )

    objects = RTDTokenManager()

    class Meta:
        ordering = ("-created",)
        verbose_name = _("API token")
        verbose_name_plural = _("API tokens")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Keep the user that created the key, even if it's renamed or deleted later.
        if self.created_by and not self.created_by_user_id:
            self.created_by_user_id = self.created_by.pk
            self.created_by_username = self.created_by.username
        super().save(*args, **kwargs)

    @property
    def has_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()

    @property
    def is_revoked(self):
        return self.revoked_at is not None

    def revoke(self):
        if not self.revoked_at:
            self.revoked_at = timezone.now()
            self.save()

    @property
    def scope(self):
        # TODO: when adding organization and user scoped keys, return the correct scope here.
        return APIKeyScope.PROJECT

    @property
    def is_project_scoped(self):
        return self.scope == APIKeyScope.PROJECT and self.project_id is not None

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
