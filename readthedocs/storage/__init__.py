"""
Provides lazy loaded storage instances for use throughout Read the Docs.

For static files storage, use django.contrib.staticfiles.storage.staticfiles_storage.
Some storage backends (notably S3) have a slow instantiation time
so doing those upfront improves performance.
"""
from django.conf import settings

from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


class ConfiguredBuildMediaStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()


class ConfiguredBuildEnvironmentStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_ENVIRONMENT_STORAGE)()


class ConfiguredBuildCommandsStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_COMMANDS_STORAGE)()


build_media_storage = ConfiguredBuildMediaStorage()
build_environment_storage = ConfiguredBuildEnvironmentStorage()
build_commands_storage = ConfiguredBuildCommandsStorage()
