from enum import StrEnum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rest_framework_api_key.crypto import KeyGenerator

from readthedocs.projects.models import Project


class ProjectPermission(models.TextChoices):
    """
    Permissions that can be granted to a project scoped API token.

    Only upload is supported for now, read and write can be added later.
    """

    UPLOAD = "project:upload", _("Upload documentation")


class APIKeyScope(StrEnum):
    """
    Scope that an API token can have.

    Currently only project scoped tokens are supported, but organization and user scoped tokens
    can be added in the future.
    """

    PROJECT = "project"


def get_platform_prefix():
    """Prefix used to identify the platform (Community or Business) a token belongs to."""
    return "rtdcom" if settings.ALLOW_PRIVATE_REPOS else "rtdorg"


def get_key_prefix(scope):
    """
    Return the prefix used to identify the platform and scope of a token.

    For example, ``rtdorg_project_`` for a project scoped token in Read the Docs Community.
    """
    return f"{get_platform_prefix()}_{scope}_"


class RTDTokenGenerator(KeyGenerator):
    """
    Generate tokens prefixed with the platform and scope of the token.

    Tokens have the form ``rtdorg_project_<random>_<secret>``.
    The ``rtdorg_project_<random>`` part is stored as the prefix to look up the token,
    the full token is hashed.
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
        """Generate a token for the object, and return the plain token."""
        key, prefix, hashed_key = self.key_generator.generate(scope=obj.scope)
        obj.prefix = prefix
        obj.hashed_key = hashed_key
        return key

    def create_key(self, **kwargs):
        """Create a token, and return a ``(RTDToken, token)`` tuple."""
        obj = self.model(**kwargs)
        key = self.assign_key(obj)
        obj.save()
        return obj, key

    def get_scope_from_key(self, key):
        """Return the scope of the token from its prefix, or ``None`` if it isn't one of our tokens."""
        for scope in APIKeyScope:
            if key.startswith(get_key_prefix(scope)):
                return scope
        return None

    def get_usable_keys(self):
        # Select the project for performance when checking permissions.
        return self.filter(revoked_at__isnull=True).select_related("project")

    def get_from_key(self, key):
        """
        Return the token object from the plain token.

        Raises ``DoesNotExist`` if the token doesn't exist, is revoked, or the secret doesn't match.
        Expiration isn't checked here, so callers can give a better error.
        """
        prefix = self.key_generator.get_prefix_from_key(key)
        obj = self.get_usable_keys().get(prefix=prefix)
        if not obj.is_valid(key):
            raise self.model.DoesNotExist("Token is not valid.")
        return obj


class RTDToken(TimeStampedModel):
    """
    API token scoped to a project, with a set of permissions.

    This is the model for all API tokens that users can create,
    other scopes (like organization or user) will be added in the future.
    """

    # Platform and scope part of the token, plus a random part (e.g. ``rtdorg_project_<random>``),
    # used to look up the token.
    prefix = models.CharField(max_length=32, unique=True, editable=False)
    hashed_key = models.CharField(max_length=150, editable=False)
    name = models.CharField(
        _("Name"),
        max_length=50,
        help_text=_("A name to identify this API token"),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tokens",
        help_text=_("Project that this API token grants access to"),
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("What this API token is used for"),
    )
    permissions = models.JSONField(
        help_text=_("List of permissions granted to this API token"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tokens",
        help_text=_("User that created this API token"),
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
        help_text=_("When the API token expires, it can't be used after this date"),
    )
    last_used_at = models.DateTimeField(
        _("Last used"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API token was last used"),
    )
    # A revoked token can't be used anymore, this can't be undone.
    revoked_at = models.DateTimeField(
        _("Revoked at"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("When the API token was revoked"),
    )

    objects = RTDTokenManager()

    class Meta(TimeStampedModel.Meta):
        ordering = ("-created",)
        verbose_name = _("API token")
        verbose_name_plural = _("API tokens")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store the initial value to detect if a revoked token is being restored.
        self._initial_revoked_at = self.revoked_at

    def __str__(self):
        return self.name

    def clean(self):
        self._validate_revoked()

    def save(self, *args, **kwargs):
        self._validate_revoked()
        # Keep the user that created the token, even if it's renamed or deleted later.
        if self.created_by and not self.created_by_user_id:
            self.created_by_user_id = self.created_by.pk
            self.created_by_username = self.created_by.username
        # The row lock taken in ``_keep_dates_from_targeted_updates()`` lasts until the transaction ends,
        # the read and the save must be in the same transaction so the dates can't change in between.
        # ``select_for_update()`` also fails outside a transaction, and requests aren't atomic.
        with transaction.atomic():
            if self.pk:
                self._keep_dates_from_targeted_updates()
            super().save(*args, **kwargs)
        self._initial_revoked_at = self.revoked_at

    def _keep_dates_from_targeted_updates(self):
        """
        Keep the revoked and last used dates from the database.

        These dates are changed with targeted updates (``revoke()`` and ``update_last_used()``),
        so saving an instance that was loaded before they changed would overwrite them.
        The row is locked until the save is done, so they can't change in between.
        """
        # ``select_for_update()`` locks the row (``SELECT ... FOR UPDATE``),
        # other updates to it, like the one in ``revoke()``, wait until this transaction ends.
        current = (
            type(self)
            .objects.select_for_update()
            .filter(pk=self.pk)
            .values("revoked_at", "last_used_at")
            .first()
        )
        if not current:
            return
        if current["revoked_at"]:
            self.revoked_at = current["revoked_at"]
        if current["last_used_at"] and (
            not self.last_used_at or current["last_used_at"] > self.last_used_at
        ):
            self.last_used_at = current["last_used_at"]

    def _validate_revoked(self):
        if self._initial_revoked_at and not self.revoked_at:
            raise ValidationError(_("The API token has been revoked, which can't be undone."))

    def is_valid(self, key):
        """
        Check if the plain token matches the hashed token.

        If the hashed token uses an outdated hasher, it's updated to use the preferred one.
        """
        key_generator = type(self).objects.key_generator
        valid = key_generator.verify(key, self.hashed_key)
        if valid and not key_generator.using_preferred_hasher(self.hashed_key):
            self.hashed_key = key_generator.hash(key)
            # Only update the hash, using the token shouldn't change its modified date.
            self.save(update_fields=["hashed_key"])
        return valid

    @property
    def has_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()

    @property
    def is_revoked(self):
        return self.revoked_at is not None

    def revoke(self):
        """
        Revoke the token, this can't be undone.

        Done with a single conditional update, so it doesn't depend on this instance being up to date,
        and a token that was already revoked keeps its original date.
        """
        now = timezone.now()
        type(self).objects.filter(pk=self.pk, revoked_at__isnull=True).update(
            revoked_at=now,
            modified=now,
        )
        self.refresh_from_db(fields=["revoked_at", "modified"])
        self._initial_revoked_at = self.revoked_at

    def update_last_used(self):
        """
        Set the date the token was last used to now.

        Done with a single conditional update, so the date only moves forward,
        and the modified date of the token isn't changed.

        .. note::

           This is a write on every request, tokens are only used by the upload API for now,
           which doesn't get many requests. If this becomes a problem,
           only update it if the last update was more than x minutes ago.
        """
        now = timezone.now()
        updated = (
            type(self)
            .objects.filter(
                models.Q(last_used_at__isnull=True) | models.Q(last_used_at__lt=now),
                pk=self.pk,
            )
            .update(last_used_at=now)
        )
        if updated:
            self.last_used_at = now
        else:
            # Another request already set a later date.
            self.refresh_from_db(fields=["last_used_at"])

    @property
    def scope(self):
        # TODO: when adding organization and user scoped tokens, return the correct scope here.
        return APIKeyScope.PROJECT

    @property
    def is_project_scoped(self):
        return self.scope == APIKeyScope.PROJECT and self.project_id is not None

    def has_permission(self, permission):
        # TODO: when adding read/write permissions, resolve implied permissions here
        # (e.g. write implies read), keep storing only the permissions that were granted.
        return permission in self.permissions

    def get_permissions_display(self):
        """Return the human readable names of the permissions of this token."""
        return [
            ProjectPermission(permission).label
            for permission in self.permissions
            if permission in ProjectPermission.values
        ]
