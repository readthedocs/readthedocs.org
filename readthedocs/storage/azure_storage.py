# pylint: disable=abstract-method
# Disable: Method 'path' is abstract in class 'Storage' but is not overridden

"""Django storage classes to use with Azure Blob storage service."""

from azure.common import AzureMissingResourceHttpError
from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from storages.backends.azure_storage import AzureStorage

from readthedocs.builds.storage import BuildMediaStorageMixin

from .mixins import OverrideHostnameMixin


class AzureBuildMediaStorage(BuildMediaStorageMixin, OverrideHostnameMixin, AzureStorage):

    """An Azure Storage backend for build artifacts."""

    azure_container = getattr(settings, 'AZURE_MEDIA_STORAGE_CONTAINER', None) or 'media'
    override_hostname = getattr(settings, 'AZURE_MEDIA_STORAGE_HOSTNAME', None)


class AzureBuildStorage(AzureStorage):

    """An Azure Storage backend for build cold storage."""

    azure_container = getattr(settings, 'AZURE_BUILD_STORAGE_CONTAINER', None) or 'builds'


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
