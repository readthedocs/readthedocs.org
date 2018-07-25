from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin

from storages.backends.azure_storage import AzureStorage


class BuildAzureStorage(AzureStorage):

    azure_container = getattr(settings, 'AZURE_BUILD_STORAGE_CONTAINER', None) or 'builds'


class MediaAzureStorage(HashedFilesMixin, AzureStorage):
    """
    A combination media & azure storage:

    * Uses Django's ManifestFilesMixin to create file manifests
    * Uploads them to our Azure container
    """

    azure_container = getattr(settings, 'AZURE_BUILD_STORAGE_CONTAINER', None) or 'media'
