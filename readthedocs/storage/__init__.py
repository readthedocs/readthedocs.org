"""
Provides lazy loaded storage instances for use throughout Read the Docs.

For static files storage, use django.contrib.staticfiles.storage.staticfiles_storage.
Some storage backends (notably S3) have a slow instantiation time
so doing those upfront improves performance.
"""

from django.core.files.storage import storages
from django.utils.functional import LazyObject


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
