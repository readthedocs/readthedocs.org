import shutil
from functools import cached_property

import structlog
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage

from readthedocs.storage.mixins import RTDBaseStorage
from readthedocs.storage.rclone import RCloneLocal
from readthedocs.storage.utils import safe_join


log = structlog.get_logger(__name__)


class RTDFileSystemStorage(RTDBaseStorage, FileSystemStorage):
    """
    Storage subclass that writes files to the local filesystem.

    .. note:: This storage is used on tests only, and it is not used in production.
    """

    def __init__(self, location=None, allow_overwrite=False, **kwargs):
        # TODO: find a better way to not pass unknown kwargs to FileSystemStorage.
        # This happens because we are creating storage instances dynamically in
        # readthedocs.projects.tasks.storage and we are passing the credentials
        # as kwargs, which are not used by FileSystemStorage.
        # NOTE: this is used on tests only.
        super().__init__(location=location, allow_overwrite=allow_overwrite)

    @cached_property
    def _rclone(self):
        return RCloneLocal(location=self.location)

    def delete_directory(self, path):
        if path in ("", "/"):
            raise SuspiciousFileOperation("Deleting all storage cannot be right")
        log.debug("Deleting directory from filesystem storage", path=path)
        abs_path = self.path(path)
        try:
            shutil.rmtree(abs_path)
        except FileNotFoundError:
            pass
        except OSError:
            log.exception("Error while deleting directory", path=abs_path)
            raise

    def url(self, name, *args, **kwargs):
        """
        Override to accept extra arguments and ignore them all.

        This method helps us to bring compatibility between Azure Blob Storage
        (which does not use the HTTP method) and Amazon S3 (who requires HTTP
        method to build the signed URL).

        ``FileSystemStorage`` does not support any other argument than ``name``.
        https://docs.djangoproject.com/en/5.2/ref/files/storage/#django.core.files.storage.Storage.url
        """
        return super().url(name)

    def listdir(self, path):
        """
        Return empty lists for nonexistent directories.

        This mimics what cloud storages do.
        """
        if not self.exists(path):
            return [], []
        return super().listdir(path)

    def join(self, directory, filepath):
        # NOTE: tests are relying on this being the one used in cloud storage backends,
        # in reality, we should use ``django.utils._os.safe_join``.
        return safe_join(directory, filepath)
