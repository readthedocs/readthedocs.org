import getpass
import logging
import os

from django.conf import settings

log = logging.getLogger(__name__)

SYNC_USER = getattr(settings, 'SYNC_USER', getpass.getuser())


def copy_to_app_servers(full_build_path, target, mkdir=True):
    """
    A helper to copy a directory across app servers
    """
    log.info("Copying %s to %s" % (full_build_path, target))
    for server in settings.MULTIPLE_APP_SERVERS:
        mkdir_cmd = ("ssh %s@%s mkdir -p %s" % (SYNC_USER, server, target))
        ret = os.system(mkdir_cmd)
        if ret != 0:
            log.error("COPY ERROR to app servers:")
            log.error(mkdir_cmd)

        sync_cmd = ("rsync -e 'ssh -T' -av --delete %s/ %s@%s:%s"
                    % (full_build_path, SYNC_USER, server, target))
        ret = os.system(sync_cmd)
        if ret != 0:
            log.error("COPY ERROR to app servers.")
            log.error(sync_cmd)


def copy_file_to_app_servers(from_file, to_file):
    """
    A helper to copy a single file across app servers
    """
    log.info("Copying %s to %s" % (from_file, to_file))
    to_path = os.path.dirname(to_file)
    for server in settings.MULTIPLE_APP_SERVERS:
        mkdir_cmd = ("ssh %s@%s mkdir -p %s" % (SYNC_USER, server, to_path))
        ret = os.system(mkdir_cmd)
        if ret != 0:
            log.error("COPY ERROR to app servers.")
            log.error(mkdir_cmd)

        sync_cmd = ("rsync -e 'ssh -T' -av --delete %s %s@%s:%s" % (from_file,
                                                                    SYNC_USER,
                                                                    server,
                                                                    to_file))
        ret = os.system(sync_cmd)
        if ret != 0:
            log.error("COPY ERROR to app servers.")
            log.error(sync_cmd)


def run_on_app_servers(command):
    """
    A helper to copy a single file across app servers
    """
    log.info("Running %s on app servers" % command)
    ret_val = 0
    if getattr(settings, "MULTIPLE_APP_SERVERS", None):
        for server in settings.MULTIPLE_APP_SERVERS:
            ret = os.system("ssh %s@%s %s" % (SYNC_USER, server, command))
            if ret != 0:
                ret_val = ret
        return ret_val
    else:
        ret = os.system(command)
        return ret
