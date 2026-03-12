"""Django storage mixin classes for different storage backends (Azure, S3)."""

from functools import cached_property
from pathlib import Path
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import structlog
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation


log = structlog.get_logger(__name__)


class RTDBaseStorage:
    """
    A common interface for all our storage backends to implement.

    This adds some convenience methods to Django's File Storage API.
    like to copy and delete entire directories efficiently,
    and interacting with rclone to sync directories to storage.

    See: https://docs.djangoproject.com/en/5.2/ref/files/storage/
    """

    def _check_suspicious_path(self, path):
        """Check that the given path isn't a symlink or outside the doc root."""
        path = Path(path)
        resolved_path = path.resolve()
        if path.is_symlink():
            msg = "Suspicious operation over a symbolic link."
            log.error(msg, path=str(path), resolved_path=str(resolved_path))
            raise SuspiciousFileOperation(msg)

        docroot = Path(settings.DOCROOT).absolute()
        if not path.is_relative_to(docroot):
            msg = "Suspicious operation outside the docroot directory."
            log.error(msg, path=str(path), resolved_path=str(resolved_path))
            raise SuspiciousFileOperation(msg)

    @cached_property
    def _rclone(self):
        raise NotImplementedError

    def rclone_sync_directory(self, source, destination):
        """Sync a directory recursively to storage using rclone sync."""
        if destination in ("", "/"):
            raise SuspiciousFileOperation("Syncing all storage cannot be right")

        self._check_suspicious_path(source)
        return self._rclone.sync(source, destination)

    def delete_directory(self, path):
        raise NotImplementedError

    def join(self, directory, filepath):
        raise NotImplementedError


class OverrideHostnameMixin:
    """
    Override the hostname when outputting URLs.

    This is useful for use with a CDN or when proxying outside of Blob Storage

    See: https://github.com/jschneier/django-storages/pull/658
    """

    override_hostname = None  # Just the hostname without scheme (eg. 'assets.readthedocs.org')

    def url(self, *args, **kwargs):
        url = super().url(*args, **kwargs)

        if self.override_hostname:
            parts = list(urlsplit(url))
            parts[1] = self.override_hostname
            url = urlunsplit(parts)

        return url


class S3PrivateBucketMixin:
    """Make the bucket private and use auth querystring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bucket_acl = "private"
        self.default_acl = "private"
        self.querystring_auth = True
