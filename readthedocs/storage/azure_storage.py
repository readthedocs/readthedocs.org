# pylint: disable=abstract-method
# Disable: Method 'path' is abstract in class 'Storage' but is not overridden

"""Django storage classes to use with Azure Blob storage service."""

import logging
from azure.common import AzureMissingResourceHttpError
from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from storages.backends.azure_storage import AzureStorage

from readthedocs.builds.storage import BuildMediaStorageMixin

from .mixins import OverrideHostnameMixin


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class AzureBuildMediaStorage(BuildMediaStorageMixin, OverrideHostnameMixin, AzureStorage):

    """An Azure Storage backend for build artifacts."""

    azure_container = getattr(settings, 'AZURE_MEDIA_STORAGE_CONTAINER', None) or 'media'
    override_hostname = getattr(settings, 'AZURE_MEDIA_STORAGE_HOSTNAME', None)

    def url(self, name, expire=None, http_method=None):  # noqa
        """
        Override to accept ``http_method`` and ignore it.

        This method helps us to bring compatibility between Azure Blob Storage
        (which does not use the HTTP method) and Amazon S3 (who requires HTTP
        method to build the signed URL).
        """
        return super().url(name, expire)

    def exists(self, name):
        """Override to catch timeout exception and return False."""
        try:
            return super().exists(name)
        except Exception:  # pylint: disable=broad-except
            log.exception('Timeout calling Azure .exists. name=%s', name)
            return False


class AzureBuildStorage(AzureStorage):

    """An Azure Storage backend for build cold storage."""

    azure_container = getattr(settings, 'AZURE_BUILD_COMMANDS_STORAGE_CONTAINER', None) or 'builds'


class AzureBuildEnvironmentStorage(BuildMediaStorageMixin, AzureStorage):

    azure_container = getattr(settings, 'AZURE_BUILD_ENVIRONMENT_STORAGE_CONTAINER', None) or 'envs'


class AzureStaticStorage(OverrideHostnameMixin, ManifestFilesMixin, AzureStorage):

    """
    An Azure Storage backend for static media.

    * Uses Django's ManifestFilesMixin to have unique file paths (eg. core.a6f5e2c.css)
    """

    azure_container = getattr(settings, 'AZURE_STATIC_STORAGE_CONTAINER', None) or 'static'
    override_hostname = getattr(settings, 'AZURE_STATIC_STORAGE_HOSTNAME', None)

    def read_manifest(self):
        """Handle a workaround to make Azure work with Django on the first 'collectstatic'."""
        try:
            return super().read_manifest()
        except AzureMissingResourceHttpError:
            # Normally Django handles this transparently as long as failing
            # to read the manifest throws an IOError. However, failing to
            # read a missing file from Azure storage doesn't currently
            return None
