"""
Classes to copy files between build and web servers.

"Syncers" copy files from the local machine, while "Pullers" copy files to the
local machine.
"""

import logging
import os
import shutil

from django.conf import settings
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


class NullSyncer:

    """A syncer that doesn't actually do anything"""

    @classmethod
    def copy(cls, path, target, is_file=False, **kwargs):
        pass  # noqa


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
        if settings.MULTIPLE_APP_SERVERS:
            log.info(
                'Remote Copy %s to %s on %s',
                path, target,
                settings.MULTIPLE_APP_SERVERS
            )
            for server in settings.MULTIPLE_APP_SERVERS:
                mkdir_cmd = (
                    'ssh {}@{} mkdir -p {}'.format(settings.SYNC_USER, server, target)
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
                        user=settings.SYNC_USER,
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
        if not is_file:
            path += '/'
        log.info('Remote Copy %s to %s', path, target)
        for server in settings.MULTIPLE_APP_SERVERS:
            if not is_file:
                mkdir_cmd = 'ssh {user}@{server} mkdir -p {target}'.format(
                    user=settings.SYNC_USER,
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
                    user=settings.SYNC_USER,
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
            user=settings.SYNC_USER,
            target=target,
        )
        ret = os.system(sync_cmd)
        if ret != 0:
            log.debug(
                'Copy error to app servers. Command: [%s] Return: [%s]',
                sync_cmd,
                ret,
            )


class Syncer(SettingsOverrideObject):
    _default_class = LocalSyncer
    _override_setting = 'FILE_SYNCER'
