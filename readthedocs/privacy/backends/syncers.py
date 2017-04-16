import getpass
import logging
import os
import shutil

from django.conf import settings

log = logging.getLogger(__name__)


class LocalSyncer(object):

    @classmethod
    def copy(cls, path, target, file=False, **kwargs):
        """
        A copy command that works with files or directories.
        """
        log.info("Local Copy %s to %s" % (path, target))
        if file:
            if path == target:
                # Don't copy the same file over itself
                return
            if os.path.exists(target):
                os.remove(target)
            shutil.copy2(path, target)
        else:
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(path, target)


class RemoteSyncer(object):

    @classmethod
    def copy(cls, path, target, file=False, **kwargs):
        """
        A better copy command that works with files or directories.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        app_servers = getattr(settings, 'MULTIPLE_APP_SERVERS', [])
        if app_servers:
            log.info("Remote Copy %s to %s" % (path, target))
            for server in app_servers:
                mkdir_cmd = ("ssh %s@%s mkdir -p %s" % (sync_user, server, target))
                ret = os.system(mkdir_cmd)
                if ret != 0:
                    log.info("COPY ERROR to app servers:")
                    log.info(mkdir_cmd)
                if file:
                    slash = ""
                else:
                    slash = "/"
                # Add a slash when copying directories
                sync_cmd = (
                    "rsync -e 'ssh -T' -av --delete {path}{slash} {user}@{server}:{target}"
                    .format(
                        path=path,
                        slash=slash,
                        user=sync_user,
                        server=server,
                        target=target))
                ret = os.system(sync_cmd)
                if ret != 0:
                    log.info("COPY ERROR to app servers.")
                    log.info(sync_cmd)


class DoubleRemotePuller(object):

    @classmethod
    def copy(cls, path, target, host, file=False, **kwargs):
        """
        A better copy command that works from the webs.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        app_servers = getattr(settings, 'MULTIPLE_APP_SERVERS', [])
        if not file:
            path += "/"
        log.info("Remote Copy %s to %s" % (path, target))
        for server in app_servers:
            if not file:
                mkdir_cmd = "ssh {user}@{server} mkdir -p {target}".format(
                    user=sync_user, server=server, target=target
                )
                ret = os.system(mkdir_cmd)
                if ret != 0:
                    log.info("MKDIR ERROR to app servers:")
                    log.info(mkdir_cmd)
            # Add a slash when copying directories
            sync_cmd = (
                "ssh {user}@{server} 'rsync -av --delete {user}@{host}:{path} {target}'"
                .format(
                    host=host,
                    path=path,
                    user=sync_user,
                    server=server,
                    target=target))
            ret = os.system(sync_cmd)
            if ret != 0:
                log.info("COPY ERROR to app servers.")
                log.info(sync_cmd)


class RemotePuller(object):

    @classmethod
    def copy(cls, path, target, host, file=False, **kwargs):
        """
        A better copy command that works from the webs.

        Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
        """
        sync_user = getattr(settings, 'SYNC_USER', getpass.getuser())
        if not file:
            path += "/"
        log.info("Local Copy %s to %s" % (path, target))
        os.makedirs(target)
        # Add a slash when copying directories
        sync_cmd = "rsync -e 'ssh -T' -av --delete {user}@{host}:{path} {target}".format(
            host=host,
            path=path,
            user=sync_user,
            target=target,
        )
        ret = os.system(sync_cmd)
        if ret != 0:
            log.info("COPY ERROR to app servers.")
