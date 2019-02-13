# -*- coding: utf-8 -*-

"""
Classes to copy files between build and web servers.

"Syncers" copy files from the local machine, while "Pullers" copy files to the
local machine.
"""

import getpass
import logging
import os
import shutil

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import get_storage_class

from readthedocs.core.utils import safe_makedirs
from readthedocs.core.utils.extend import SettingsOverrideObject


log = logging.getLogger(__name__)
storage = get_storage_class()()


class BaseSyncer:

    """A base object for syncers and pullers."""

    @classmethod
    def copy(cls, path, target, is_file=False, **kwargs):
        raise NotImplementedError


class LocalSyncer(BaseSyncer):

    @classmethod
    def copy(cls, path, target, is_file=False, **kwargs):
        """A copy command that works with files or directories."""
        log.info('Local Copy %s to %s', path, target)
        if is_file:
            if path == target:
                # Don't copy the same file over itself
                return
            if os.path.exists(target):
                os.remove(target)

            # Create containing directory if it doesn't exist
            directory = os.path.dirname(target)
            safe_makedirs(directory)

            shutil.copy2(path, target)
        else:
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(path, target)


class RemoteSyncer(BaseSyncer):

    @classmethod
    def copy(cls, path, target, is_file=False, **kwargs):
        """
        A better copy command that works with files or directories.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        app_servers = getattr(settings, 'MULTIPLE_APP_SERVERS', [])
        if app_servers:
            log.info('Remote Copy %s to %s on %s', path, target, app_servers)
            for server in app_servers:
                mkdir_cmd = (
                    'ssh {}@{} mkdir -p {}'.format(sync_user, server, target)
                )
                ret = os.system(mkdir_cmd)
                if ret != 0:
                    log.debug('Copy error to app servers: cmd=%s', mkdir_cmd)
                if is_file:
                    slash = ''
                else:
                    slash = '/'
                # Add a slash when copying directories
                sync_cmd = (
                    "rsync -e 'ssh -T' -av --delete {path}{slash} {user}@{server}:{target}".format(
                        path=path,
                        slash=slash,
                        user=sync_user,
                        server=server,
                        target=target,
                    )
                )
                ret = os.system(sync_cmd)
                if ret != 0:
                    log.debug('Copy error to app servers: cmd=%s', sync_cmd)


class DoubleRemotePuller(BaseSyncer):

    @classmethod
    def copy(cls, path, target, host, is_file=False, **kwargs):  # pylint: disable=arguments-differ
        """
        A better copy command that works from the webs.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        app_servers = getattr(settings, 'MULTIPLE_APP_SERVERS', [])
        if not is_file:
            path += '/'
        log.info('Remote Copy %s to %s', path, target)
        for server in app_servers:
            if not is_file:
                mkdir_cmd = 'ssh {user}@{server} mkdir -p {target}'.format(
                    user=sync_user,
                    server=server,
                    target=target,
                )
                ret = os.system(mkdir_cmd)
                if ret != 0:
                    log.debug('MkDir error to app servers: cmd=%s', mkdir_cmd)
            # Add a slash when copying directories
            sync_cmd = (
                "ssh {user}@{server} 'rsync -av "
                "--delete --exclude projects {user}@{host}:{path} {target}'".format(
                    host=host,
                    path=path,
                    user=sync_user,
                    server=server,
                    target=target,
                )
            )
            ret = os.system(sync_cmd)
            if ret != 0:
                log.debug('Copy error to app servers: cmd=%s', sync_cmd)


class RemotePuller(BaseSyncer):

    @classmethod
    def copy(cls, path, target, host, is_file=False, **kwargs):  # pylint: disable=arguments-differ
        """
        A better copy command that works from the webs.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        if not is_file:
            path += '/'
        log.info('Remote Pull %s to %s', path, target)
        if not is_file and not os.path.exists(target):
            safe_makedirs(target)
        if is_file:
            # Create containing directory if it doesn't exist
            directory = os.path.dirname(target)
            safe_makedirs(directory)
        # Add a slash when copying directories
        sync_cmd = "rsync -e 'ssh -T' -av --delete {user}@{host}:{path} {target}".format(
            host=host,
            path=path,
            user=sync_user,
            target=target,
        )
        ret = os.system(sync_cmd)
        if ret != 0:
            log.debug(
                'Copy error to app servers. Command: [%s] Return: [%s]',
                sync_cmd,
                ret,
            )


class SelectiveStorageRemotePuller(RemotePuller):

    """
    Exactly like RemotePuller except that certain files are copied via Django's storage system

    If a file with extensions specified by ``extensions`` is copied, it will be copied to storage
    and the original is removed.

    See: https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-DEFAULT_FILE_STORAGE
    """

    extensions = ('.pdf', '.epub', '.zip')

    @classmethod
    def get_storage_path(cls, path):
        """
        Gets the path to the file within the storage engine

        For example, if the path was $MEDIA_ROOT/pdfs/latest.pdf
         the storage_path is 'pdfs/latest.pdf'

        :raises: SuspiciousFileOperation if the path isn't under settings.MEDIA_ROOT
        """
        path = os.path.normpath(path)
        if not path.startswith(settings.MEDIA_ROOT):
            raise SuspiciousFileOperation

        path = path.replace(settings.MEDIA_ROOT, '').lstrip('/')
        return path

    @classmethod
    def copy(cls, path, target, host, is_file=False, **kwargs):  # pylint: disable=arguments-differ
        RemotePuller.copy(path, target, host, is_file, **kwargs)

        if getattr(storage, 'write_build_media', False):
            # This is a sanity check for the case where
            # storage is backed by the local filesystem
            # In that case, removing the original target file locally
            # would remove the file from storage as well

            if is_file and os.path.exists(target) and \
                    any([target.lower().endswith(ext) for ext in cls.extensions]):
                log.info("Selective Copy %s to media storage", target)

                storage_path = cls.get_storage_path(target)

                if storage.exists(storage_path):
                    storage.delete(storage_path)

                with open(target, 'rb') as fd:
                    storage.save(storage_path, fd)


class Syncer(SettingsOverrideObject):
    _default_class = LocalSyncer
    _override_setting = 'FILE_SYNCER'
