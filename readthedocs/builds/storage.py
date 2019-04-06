import logging
from pathlib import Path

from storages.utils import safe_join, get_available_overwrite_name


log = logging.getLogger(__name__)


class BuildMediaStorageMixin:

    """
    A mixin for Storage classes needed to write build artifacts

    This adds and modifies some functionality to Django's File Storage API.
    By default, classes mixing this in will now overwrite files by default instead
    of finding an available name.
    This adds functionality to copy and delete entire directories.

    See: https://docs.djangoproject.com/en/1.11/ref/files/storage
    """

    @staticmethod
    def _dirpath(path):
        """It may just be Azure, but for listdir to work correctly, the path must end in '/'"""
        path = str(path)
        if not path.endswith('/'):
            path += '/'

        return path

    def get_available_name(self, name, max_length=None):
        """
        Overrides Django's storage implementation to always return the passed name (overwrite)

        By default, Django will not overwrite files even if the same name is specified.
        This changes that functionality so that the default is to use the same name and overwrite
        rather than modify the path to not clobber files.
        """
        return get_available_overwrite_name(name, max_length=max_length)

    def delete_directory(self, path):
        """
        Delete all files under a certain path from storage

        Many storage backends (S3, Azure storage) don't care about "directories".
        The directory effectively doesn't exist if there are no files in it.
        However, in these backends, there is no "rmdir" operation so you have to recursively
        delete all files.

        :param path: the path to the directory to remove
        """
        log.debug('Deleting directory %s from media storage', path)
        folders, files = self.listdir(self._dirpath(path))
        for folder_name in folders:
            if folder_name:
                # Recursively delete the subdirectory
                self.delete_directory(safe_join(path, folder_name))
        for filename in files:
            if filename:
                self.delete(safe_join(path, filename))

    def copy_directory(self, source, destination):
        """
        Copy a directory recursively to storage

        :param source: the source path on the local disk
        :param destination: the destination path in storage
        """
        log.debug('Copying source directory %s to media storage at %s', source, destination)
        source = Path(source)
        for filepath in source.iterdir():
            sub_destination = safe_join(destination, filepath.name)
            if filepath.is_dir():
                # Recursively copy the subdirectory
                self.copy_directory(filepath, sub_destination)
            elif filepath.is_file():
                with filepath.open('rb') as fd:
                    self.save(sub_destination, fd)
