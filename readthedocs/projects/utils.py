"""Utility functions used by projects"""

import fnmatch
import os
import subprocess
import traceback
import logging
from httplib2 import Http

import redis
from django.conf import settings
from django.core.cache import cache


log = logging.getLogger(__name__)


def version_from_slug(slug, version):
    from readthedocs.projects import tasks
    from readthedocs.builds.models import Version
    from readthedocs.restapi.client import api
    if getattr(settings, 'DONT_HIT_DB', True):
        version_data = api.version().get(project=slug, slug=version)['results'][0]
        v = tasks.make_api_version(version_data)
    else:
        v = Version.objects.get(project__slug=slug, slug=version)
    return v


def update_static_metadata(project_pk):
    """This is here to avoid circular imports in models.py"""
    from readthedocs.projects import tasks
    tasks.update_static_metadata.delay(project_pk)


def find_file(filename):
    """Recursively find matching file from the current working path

    :param file: Filename to match
    :returns: A list of matching filenames.
    """
    matches = []
    for root, __, filenames in os.walk('.'):
        for filename in fnmatch.filter(filenames, filename):
            matches.append(os.path.join(root, filename))
    return matches


def run(*commands, **kwargs):
    """Run one or more commands

    If more than one command is given, then this is equivalent to
    chaining them together with ``&&``; if all commands succeed, then
    ``(status, out, err)`` will represent the last successful command.
    If one command failed, then ``(status, out, err)`` will represent
    the failed command.

    :returns: ``(status, out, err)``
    """
    environment = os.environ.copy()
    environment['READTHEDOCS'] = 'True'
    if 'DJANGO_SETTINGS_MODULE' in environment:
        del environment['DJANGO_SETTINGS_MODULE']
    if 'PYTHONPATH' in environment:
        del environment['PYTHONPATH']
    # Remove PYTHONHOME env variable if set, otherwise pip install of requirements
    # into virtualenv will install incorrectly
    if 'PYTHONHOME' in environment:
        del environment['PYTHONHOME']
    cwd = os.getcwd()
    if not commands:
        raise ValueError("run() requires one or more command-line strings")
    shell = kwargs.get('shell', False)

    for command in commands:
        if shell:
            log.info("Running commands in a shell")
            run_command = command
        else:
            run_command = command.split()
        log.info("Running: '%s' [%s]", command, cwd)
        try:
            p = subprocess.Popen(run_command, shell=shell, cwd=cwd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=environment)

            out, err = p.communicate()
            ret = p.returncode
        except OSError:
            out = ''
            err = traceback.format_exc()
            ret = -1
            log.error("Command failed", exc_info=True)

    return (ret, out, err)


def safe_write(filename, contents):
    """Normalize and write to filename

    Write ``contents`` to the given ``filename``. If the filename's
    directory does not exist, it is created. Contents are written as UTF-8,
    ignoring any characters that cannot be encoded as UTF-8.

    :param filename: Filename to write to
    :param contents: File contents to write to file
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as fh:
        fh.write(contents.encode('utf-8', 'ignore'))
        fh.close()


def purge_version(version, mainsite=False, subdomain=False, cname=False):
    varnish_servers = getattr(settings, 'VARNISH_SERVERS', None)
    h = Http()
    if varnish_servers:
        for server in varnish_servers:
            if subdomain:
                # Send a request to the Server, to purge the URL of the Host.
                host = "%s.readthedocs.org" % version.project.slug
                headers = {'Host': host}
                url = "/en/%s/*" % version.slug
                to_purge = "http://%s%s" % (server, url)
                log.info("Purging %s on %s", url, host)
                h.request(to_purge, method="PURGE", headers=headers)
            if mainsite:
                headers = {'Host': "readthedocs.org"}
                url = "/docs/%s/en/%s/*" % (version.project.slug, version.slug)
                to_purge = "http://%s%s" % (server, url)
                log.info("Purging %s on readthedocs.org", url)
                h.request(to_purge, method="PURGE", headers=headers)
                root_url = "/docs/%s/" % version.project.slug
                to_purge = "http://%s%s" % (server, root_url)
                log.info("Purging %s on readthedocs.org", root_url)
                h.request(to_purge, method="PURGE", headers=headers)
            if cname:
                try:
                    redis_client = cache.get_client(None)
                    for cnamed in redis_client.smembers('rtd_slug:v1:%s'
                                                        % version.project.slug):
                        headers = {'Host': cnamed}
                        url = "/en/%s/*" % version.slug
                        to_purge = "http://%s%s" % (server, url)
                        log.info("Purging %s on %s", url, cnamed)
                        h.request(to_purge, method="PURGE", headers=headers)
                        root_url = "/"
                        to_purge = "http://%s%s" % (server, root_url)
                        log.info("Purging %s on %s", root_url, cnamed)
                        h.request(to_purge, method="PURGE", headers=headers)
                except (AttributeError, redis.exceptions.ConnectionError):
                    pass


class DictObj(object):

    def __getattr__(self, attr):
        return self.__dict__.get(attr)


# Prevent saving the temporary Project instance
def _new_save(*dummy_args, **dummy_kwargs):
    log.warning("Called save on a non-real object.")
    return 0


def make_api_version(version_data):
    """Make mock Version instance from API return"""
    from readthedocs.builds.models import Version
    for key in ['resource_uri', 'absolute_url', 'downloads']:
        if key in version_data:
            del version_data[key]
    project_data = version_data['project']
    project = make_api_project(project_data)
    version_data['project'] = project
    ver = Version(**version_data)
    ver.save = _new_save

    return ver


def make_api_project(project_data):
    """Make mock Project instance from API return"""
    from readthedocs.projects.models import Project
    for key in ['users', 'resource_uri', 'absolute_url', 'downloads',
                'main_language_project', 'related_projects']:
        if key in project_data:
            del project_data[key]
    project = Project(**project_data)
    project.save = _new_save
    return project
