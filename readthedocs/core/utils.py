import getpass
import logging
import os
import shutil

from urlparse import urlparse

from django.conf import settings

log = logging.getLogger(__name__)

SYNC_USER = getattr(settings, 'SYNC_USER', getpass.getuser())

def copy(path, target, file=False):
    """
    A better copy command that works with files or directories.

    Respects the ``MULTIPLE_APP_SERVERS`` setting when copying.
    """
    MULTIPLE_APP_SERVERS = getattr(settings, 'MULTIPLE_APP_SERVERS', [])
    if MULTIPLE_APP_SERVERS:
        log.info("Remote Copy %s to %s" % (path, target))
        for server in MULTIPLE_APP_SERVERS:
            mkdir_cmd = ("ssh %s@%s mkdir -p %s" % (SYNC_USER, server, target))
            ret = os.system(mkdir_cmd)
            if ret != 0:
                log.error("COPY ERROR to app servers:")
                log.error(mkdir_cmd)

            if file:
                slash = ""
            else:
                slash = "/"
            # Add a slash when copying directories
            sync_cmd = ("rsync -e 'ssh -T' -av --delete %s%s %s@%s:%s"
                        % (path, slash, SYNC_USER, server, target))
            ret = os.system(sync_cmd)
            if ret != 0:
                log.error("COPY ERROR to app servers.")
                log.error(sync_cmd)
    else:
        log.info("Local Copy %s to %s" % (path, target))
        if file:
            if os.path.exists(target):
                os.remove(target)
            shutil.copy2(path, target)
        else:
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(path, target)

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

def make_latest(project):
    """
    Useful for correcting versions with no latest, using the database.

    >>> no_latest = Project.objects.exclude(versions__slug__in=['latest'])
    >>> for project in no_latest:
    >>>     make_latest(project)
    """
    branch = project.default_branch or project.vcs_repo().fallback_branch
    version_data, created = Version.objects.get_or_create(
        project=project,
        slug='latest',
        type='branch',
        active=True,
        verbose_name='latest',
        identifier=branch,
    )


def clean_url(url):
    parsed = urlparse(url)
    if parsed.scheme:
        scheme, netloc = parsed.scheme, parsed.netloc
    elif parsed.netloc:
        scheme, netloc = "http", parsed.netloc
    else:
        scheme, netloc = "http", parsed.path
    return netloc

def cname_to_slug(host):
    from dns import resolver
    answer = [ans for ans in resolver.query(host, 'CNAME')][0]
    domain = answer.target.to_unicode()
    slug = domain.split('.')[0]
    return slug
