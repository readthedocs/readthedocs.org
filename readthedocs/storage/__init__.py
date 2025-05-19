"""
Provides lazy loaded storage instances for use throughout Read the Docs.

For static files storage, use django.contrib.staticfiles.storage.staticfiles_storage.
Some storage backends (notably S3) have a slow instantiation time
so doing those upfront improves performance.
"""

from django.conf import settings
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


# Borrowed from Django 4.2 since it was deprecrated and removed in 5.2
# NOTE: we can use settings.STORAGES for our own storages as well if we want to use the standards.
#
# https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STORAGES)
# https://github.com/django/django/blob/4.2/django/core/files/storage/__init__.py#L31
def get_storage_class(import_path=None):
    return import_string(import_path or settings.DEFAULT_FILE_STORAGE)


class ConfiguredBuildMediaStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()


class ConfiguredBuildCommandsStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_COMMANDS_STORAGE)()


class ConfiguredBuildToolsStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_BUILD_TOOLS_STORAGE)()


class ConfiguredStaticStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(settings.RTD_STATICFILES_STORAGE)()


build_media_storage = ConfiguredBuildMediaStorage()
build_commands_storage = ConfiguredBuildCommandsStorage()
build_tools_storage = ConfiguredBuildToolsStorage()
staticfiles_storage = ConfiguredStaticStorage()
