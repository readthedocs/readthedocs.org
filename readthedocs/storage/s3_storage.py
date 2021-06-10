"""
AWS S3 Storage backends.

We override the backends provided by django-storages to add some small pieces
that we need to make our project to work as we want. For example, using
ManifestFilesMixin for static files and OverrideHostnameMixin to make it work
in our Docker Development environment.
"""

# Disable abstract method because we are not overriding all the methods
# pylint: disable=abstract-method
from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from django.core.exceptions import ImproperlyConfigured
from storages.backends.s3boto3 import S3Boto3Storage

from readthedocs.builds.storage import BuildMediaStorageMixin

from .mixins import OverrideHostnameMixin, S3PrivateBucketMixin


class S3BuildMediaStorage(BuildMediaStorageMixin, OverrideHostnameMixin, S3Boto3Storage):

    """An AWS S3 Storage backend for build artifacts."""

    bucket_name = getattr(settings, 'S3_MEDIA_STORAGE_BUCKET', None)
    override_hostname = getattr(settings, 'S3_MEDIA_STORAGE_OVERRIDE_HOSTNAME', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                'AWS S3 not configured correctly. '
                'Ensure S3_MEDIA_STORAGE_BUCKET is defined.',
            )


class S3BuildCommandsStorage(S3PrivateBucketMixin, S3Boto3Storage):

    """An AWS S3 Storage backend for build commands."""

    bucket_name = getattr(settings, 'S3_BUILD_COMMANDS_STORAGE_BUCKET', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                'AWS S3 not configured correctly. '
                'Ensure S3_BUILD_COMMANDS_STORAGE_BUCKET is defined.',
            )


class S3StaticStorage(OverrideHostnameMixin, ManifestFilesMixin, S3Boto3Storage):

    """
    An AWS S3 Storage backend for static media.

    * Uses Django's ManifestFilesMixin to have unique file paths (eg. core.a6f5e2c.css)
    """

    bucket_name = getattr(settings, 'S3_STATIC_STORAGE_BUCKET', None)
    override_hostname = getattr(settings, 'S3_STATIC_STORAGE_OVERRIDE_HOSTNAME', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                'AWS S3 not configured correctly. '
                'Ensure S3_STATIC_STORAGE_BUCKET is defined.',
            )

        self.bucket_acl = 'public-read'
        self.default_acl = 'public-read'
        self.querystring_auth = False


class S3BuildEnvironmentStorage(S3PrivateBucketMixin, BuildMediaStorageMixin, S3Boto3Storage):

    bucket_name = getattr(settings, 'S3_BUILD_ENVIRONMENT_STORAGE_BUCKET', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.bucket_name:
            raise ImproperlyConfigured(
                'AWS S3 not configured correctly. '
                'Ensure S3_BUILD_ENVIRONMENT_STORAGE_BUCKET is defined.',
            )
