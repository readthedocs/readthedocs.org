"""
Provides lazy loaded storage instances for use throughout Read the Docs.

For static files storage, use django.contrib.staticfiles.storage.staticfiles_storage.
Some storage backends (notably S3) have a slow instantiation time
so doing those upfront improves performance.
"""

import warnings

from django.core.files.storage import storages
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


def get_storage_class(import_path=None):
    """
    Get a storage class from an import path.

    .. deprecated::
        This function is deprecated. Use Django's ``storages`` API instead:
        ``from django.core.files.storage import storages``
        and access storage by alias: ``storages["build-media"]``
    """
    warnings.warn(
        "get_storage_class is deprecated. Use Django's storages API instead: "
        "from django.core.files.storage import storages; storages['alias']",
        DeprecationWarning,
        stacklevel=2,
    )
    from django.conf import settings as django_settings

    return import_string(import_path or django_settings.DEFAULT_FILE_STORAGE)


class ConfiguredBuildMediaStorage(LazyObject):
    def _setup(self):
        self._wrapped = storages["build-media"]


class ConfiguredBuildCommandsStorage(LazyObject):
    def _setup(self):
        self._wrapped = storages["build-commands"]


class ConfiguredBuildToolsStorage(LazyObject):
    def _setup(self):
        self._wrapped = storages["build-tools"]


class ConfiguredStaticStorage(LazyObject):
    def _setup(self):
        self._wrapped = storages["staticfiles"]


build_media_storage = ConfiguredBuildMediaStorage()
build_commands_storage = ConfiguredBuildCommandsStorage()
build_tools_storage = ConfiguredBuildToolsStorage()
staticfiles_storage = ConfiguredStaticStorage()
