"""
AWS S3 Storage backends.

We override the backends provided by django-storages to add some small pieces
that we need to make our project to work as we want. For example, using
ManifestFilesMixin for static files and OverrideHostnameMixin to make it work
in our Docker Development environment.
"""

# Disable abstract method because we are not overriding all the methods
# pylint: disable=abstract-method
from functools import cached_property

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from storages.backends.s3boto3 import S3Boto3Storage
from storages.backends.s3boto3 import S3ManifestStaticStorage

from readthedocs.builds.storage import BuildMediaStorageMixin
from readthedocs.storage.rclone import RCloneS3Remote

from .mixins import OverrideHostnameMixin
from .mixins import S3PrivateBucketMixin


class S3BuildMediaStorage(OverrideHostnameMixin, BuildMediaStorageMixin, S3Boto3Storage):
    """An AWS S3 Storage backend for build artifacts."""

    bucket_name = getattr(settings, "S3_MEDIA_STORAGE_BUCKET", None)
    override_hostname = getattr(settings, "S3_MEDIA_STORAGE_OVERRIDE_HOSTNAME", None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                "AWS S3 not configured correctly. Ensure S3_MEDIA_STORAGE_BUCKET is defined.",
            )

    @cached_property
    def _rclone(self):
        provider = settings.S3_PROVIDER

        return RCloneS3Remote(
            bucket_name=self.bucket_name,
            access_key_id=self.access_key,
            secret_access_key=self.secret_key,
            session_token=self.security_token,
            region=self.region_name or "",
            acl=self.default_acl,
            endpoint=self.endpoint_url,
            provider=provider,
        )


class S3BuildCommandsStorage(S3PrivateBucketMixin, S3Boto3Storage):
    """An AWS S3 Storage backend for build commands."""

    bucket_name = getattr(settings, "S3_BUILD_COMMANDS_STORAGE_BUCKET", None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                "AWS S3 not configured correctly. "
                "Ensure S3_BUILD_COMMANDS_STORAGE_BUCKET is defined.",
            )


class S3StaticStorageMixin:
    bucket_name = getattr(settings, "S3_STATIC_STORAGE_BUCKET", None)
    override_hostname = getattr(settings, "S3_STATIC_STORAGE_OVERRIDE_HOSTNAME", None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                "AWS S3 not configured correctly. Ensure S3_STATIC_STORAGE_BUCKET is defined.",
            )

        self.querystring_auth = False


# pylint: disable=too-many-ancestors
class S3StaticStorage(
    S3StaticStorageMixin, OverrideHostnameMixin, S3ManifestStaticStorage, S3Boto3Storage
):
    """
    An AWS S3 Storage backend for static media.

    * Uses Django's ManifestFilesMixin to have unique file paths (eg. core.a6f5e2c.css)
    """


class NoManifestS3StaticStorage(S3StaticStorageMixin, OverrideHostnameMixin, S3Boto3Storage):
    """
    Storage backend for static files used outside Django's static files.

    This is the same as S3StaticStorage, but without inheriting from S3ManifestStaticStorage,
    this way we can get the URL of any file in that bucket, even hashed ones.
    """

    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito-static"


class S3BuildToolsStorage(S3PrivateBucketMixin, S3Boto3Storage):
    bucket_name = getattr(settings, "S3_BUILD_TOOLS_STORAGE_BUCKET", None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                "AWS S3 not configured correctly. Ensure S3_BUILD_TOOLS_STORAGE_BUCKET is defined.",
            )
