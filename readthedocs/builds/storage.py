from functools import cached_property
from pathlib import Path

import structlog
from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage as BaseStaticFilesStorage
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from storages.utils import get_available_overwrite_name

from readthedocs.core.utils.filesystem import safe_open
from readthedocs.storage.rclone import RCloneLocal
from readthedocs.storage.utils import safe_join


log = structlog.get_logger(__name__)


class BuildMediaStorageMixin:
    """
    A mixin for Storage classes needed to write build artifacts.

    This adds and modifies some functionality to Django's File Storage API.
    By default, classes mixing this in will now overwrite files by default instead
    of finding an available name.
    This mixin also adds convenience methods to copy and delete entire directories.

    See: https://docs.djangoproject.com/en/1.11/ref/files/storage
    """

    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito"

    @staticmethod
    def _dirpath(path):
        """
        Make the path to end with `/`.

        It may just be Azure, but for listdir to work correctly, this is needed.
        """
        path = str(path)
        if not path.endswith("/"):
            path += "/"

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
        if path in ("", "/"):
            raise SuspiciousFileOperation("Deleting all storage cannot be right")

        log.debug("Deleting path from media storage", path=path)
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
        log.debug(
            "Copying source directory to media storage",
            source=source,
            destination=destination,
        )
        source = Path(source)
        self._check_suspicious_path(source)
        for filepath in source.iterdir():
            sub_destination = self.join(destination, filepath.name)

            # Don't follow symlinks when uploading to storage.
            if filepath.is_symlink():
                log.info(
                    "Skipping symlink upload.",
                    path_resolved=str(filepath.resolve()),
                )
                continue

            if filepath.is_dir():
                # Recursively copy the subdirectory
                self.copy_directory(filepath, sub_destination)
            elif filepath.is_file():
                with safe_open(filepath, "rb") as fd:
                    self.save(sub_destination, fd)

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

    def join(self, directory, filepath):
        return safe_join(directory, filepath)

    def walk(self, top):
        if top in ("", "/"):
            raise SuspiciousFileOperation("Iterating all storage cannot be right")

        log.debug("Walking path in media storage", path=top)
        folders, files = self.listdir(self._dirpath(top))

        yield top, folders, files

        for folder_name in folders:
            if folder_name:
                # Recursively walk the subdirectory
                yield from self.walk(self.join(top, folder_name))


class BuildMediaFileSystemStorage(BuildMediaStorageMixin, FileSystemStorage):
    """Storage subclass that writes build artifacts in PRODUCTION_MEDIA_ARTIFACTS or MEDIA_ROOT."""

    def __init__(self, **kwargs):
        location = kwargs.pop("location", None)

        if not location:
            # Mirrors the logic of getting the production media path
            if settings.DEFAULT_PRIVACY_LEVEL == "public" or settings.DEBUG:
                location = settings.MEDIA_ROOT
            else:
                location = settings.PRODUCTION_MEDIA_ARTIFACTS

        super().__init__(location)

    @cached_property
    def _rclone(self):
        return RCloneLocal(location=self.location)

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

    def url(self, name, *args, **kwargs):  # noqa
        """
        Override to accept extra arguments and ignore them all.

        This method helps us to bring compatibility between Azure Blob Storage
        (which does not use the HTTP method) and Amazon S3 (who requires HTTP
        method to build the signed URL).

        ``FileSystemStorage`` does not support any other argument than ``name``.
        https://docs.djangoproject.com/en/2.2/ref/files/storage/#django.core.files.storage.Storage.url
        """
        return super().url(name)


class StaticFilesStorage(BaseStaticFilesStorage):
    # Root path of the nginx internal redirect
    # that will serve files from this storage.
    internal_redirect_root_path = "proxito-static"
