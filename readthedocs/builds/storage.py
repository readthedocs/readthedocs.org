import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from storages.utils import get_available_overwrite_name, safe_join

log = logging.getLogger(__name__)


class BuildMediaStorageMixin:

    """
    A mixin for Storage classes needed to write build artifacts.

    This adds and modifies some functionality to Django's File Storage API.
    By default, classes mixing this in will now overwrite files by default instead
    of finding an available name.
    This mixin also adds convenience methods to copy and delete entire directories.

    See: https://docs.djangoproject.com/en/1.11/ref/files/storage
    """

    @staticmethod
    def _dirpath(path):
        """
        Make the path to end with `/`.

        It may just be Azure, but for listdir to work correctly, this is needed.
        """
        path = str(path)
        if not path.endswith('/'):
            path += '/'

        return path

    def get_available_name(self, name, max_length=None):
        """
        Overrides Django's storage to always return the passed name (overwrite).

        By default, Django will not overwrite files even if the same name is specified.
        This changes that functionality so that the default is to use the same name and overwrite
        rather than modify the path to not clobber files.
        """
        return get_available_overwrite_name(name, max_length=max_length)

    def delete_directory(self, path):
        """
        Delete all files under a certain path from storage.

        Many storage backends (S3, Azure storage) don't care about "directories".
        The directory effectively doesn't exist if there are no files in it.
        However, in these backends, there is no "rmdir" operation so you have to recursively
        delete all files.

        :param path: the path to the directory to remove
        """
        if path in ('', '/'):
            raise SuspiciousFileOperation('Deleting all storage cannot be right')

        log.debug('Deleting directory %s from media storage', path)
        folders, files = self.listdir(self._dirpath(path))
        for folder_name in folders:
            if folder_name:
                # Recursively delete the subdirectory
                self.delete_directory(self.join(path, folder_name))
        for filename in files:
            if filename:
                self.delete(self.join(path, filename))

    def copy_directory(self, source, destination):
        """
        Copy a directory recursively to storage.

        :param source: the source path on the local disk
        :param destination: the destination path in storage
        """
        log.debug('Copying source directory %s to media storage at %s', source, destination)
        source = Path(source)
        for filepath in source.iterdir():
            sub_destination = self.join(destination, filepath.name)
            if filepath.is_dir():
                # Recursively copy the subdirectory
                self.copy_directory(filepath, sub_destination)
            elif filepath.is_file():
                with filepath.open('rb') as fd:
                    self.save(sub_destination, fd)

    def sync_directory(self, source, destination):
        """
        Sync a directory recursively to storage.

        Overwrites files in remote storage where a file in ``source`` exists (no timstamp checking done).
        Removes files and folders in remote storage that are not present in ``source``.

        :param source: the source path on the local disk
        :param destination: the destination path in storage
        """

        log.debug(
            'Syncing to media storage. source=%s destination=%s',
            source, destination,
        )
        source = Path(source)
        copied_files = set()
        copied_dirs = set()
        for filepath in source.iterdir():
            sub_destination = self.join(destination, filepath.name)
            if filepath.is_dir():
                # Recursively sync the subdirectory
                self.sync_directory(filepath, sub_destination)
                copied_dirs.add(filepath.name)
            elif filepath.is_file():
                with filepath.open('rb') as fd:
                    self.save(sub_destination, fd)
                copied_files.add(filepath.name)

        # Remove files that are not present in ``source``
        dest_folders, dest_files = self.listdir(self._dirpath(destination))
        for folder in dest_folders:
            if folder not in copied_dirs:
                self.delete_directory(self.join(destination, folder))
        for filename in dest_files:
            if filename not in copied_files:
                self.delete(self.join(destination, filename))

    def join(self, directory, filepath):
        return safe_join(directory, filepath)

    def walk(self, top):
        if top in ('', '/'):
            raise SuspiciousFileOperation('Iterating all storage cannot be right')

        log.debug('Walking %s in media storage', top)
        folders, files = self.listdir(self._dirpath(top))

        yield top, folders, files

        for folder_name in folders:
            if folder_name:
                # Recursively walk the subdirectory
                yield from self.walk(self.join(top, folder_name))


class BuildMediaFileSystemStorage(BuildMediaStorageMixin, FileSystemStorage):

    """Storage subclass that writes build artifacts in PRODUCTION_MEDIA_ARTIFACTS or MEDIA_ROOT."""

    def __init__(self, **kwargs):
        location = kwargs.pop('location', None)

        if not location:
            # Mirrors the logic of getting the production media path
            if settings.DEFAULT_PRIVACY_LEVEL == 'public' or settings.DEBUG:
                location = settings.MEDIA_ROOT
            else:
                location = settings.PRODUCTION_MEDIA_ARTIFACTS

        super().__init__(location)

    def get_available_name(self, name, max_length=None):
        """
        A hack to overwrite by default with the FileSystemStorage.

        After upgrading to Django 2.2, this method can be removed
        because subclasses can set OS_OPEN_FLAGS such that FileSystemStorage._save
        will properly overwrite files.
        See: https://github.com/django/django/pull/8476
        """
        name = super().get_available_name(name, max_length=max_length)
        if self.exists(name):
            self.delete(name)
        return name

    def listdir(self, path):
        """
        Return empty lists for nonexistent directories.

        This mimics what cloud storages do.
        """
        if not self.exists(path):
            return [], []
        return super().listdir(path)
