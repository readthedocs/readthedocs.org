"""Utility functions used by projects.
"""
import fnmatch
import os
import re
import subprocess
import traceback
import logging
from httplib2 import Http

from django.conf import settings

from distutils2.version import NormalizedVersion, suggest_normalized_version
import redis


log = logging.getLogger(__name__)


def find_file(file):
    """Find matching filenames in the current directory and its subdirectories,
    and return a list of matching filenames.
    """
    matches = []
    for root, dirnames, filenames in os.walk('.'):
        for filename in fnmatch.filter(filenames, file):
            matches.append(os.path.join(root, filename))
    return matches


def run(*commands, **kwargs):
    """
    Run one or more commands, and return ``(status, out, err)``.
    If more than one command is given, then this is equivalent to
    chaining them together with ``&&``; if all commands succeed, then
    ``(status, out, err)`` will represent the last successful command.
    If one command failed, then ``(status, out, err)`` will represent
    the failed command.
    """
    environment = os.environ.copy()
    environment['READTHEDOCS'] = 'True'
    if 'DJANGO_SETTINGS_MODULE' in environment:
        del environment['DJANGO_SETTINGS_MODULE']
    if 'PYTHONPATH' in environment:
        del environment['PYTHONPATH']
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
        log.info("Running: '%s'" % command)
        try:
            p = subprocess.Popen(run_command, shell=shell, cwd=cwd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=environment)

            out, err = p.communicate()
            ret = p.returncode
        except:
            out = ''
            err = traceback.format_exc()
            ret = -1
            log.error("Command failed", exc_info=True)

    return (ret, out, err)


def safe_write(filename, contents):
    """Write ``contents`` to the given ``filename``. If the filename's
    directory does not exist, it is created. Contents are written as UTF-8,
    ignoring any characters that cannot be encoded as UTF-8.
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as fh:
        fh.write(contents.encode('utf-8', 'ignore'))
        fh.close()


CUSTOM_SLUG_RE = re.compile(r'[^-._\w]+$')


def _custom_slugify(data):
    return CUSTOM_SLUG_RE.sub('', data)


def slugify_uniquely(model, initial, field, max_length, **filters):
    slug = _custom_slugify(initial)[:max_length]
    current = slug
    base_qs = model.objects.filter(**filters)
    index = 0
    while base_qs.filter(**{field: current}).exists():
        suffix = '-%s' % index
        current = '%s%s'  % (slug, suffix)
        index += 1
    return current


def mkversion(version_obj):
    try:
        if hasattr(version_obj, 'slug'):
            ver = NormalizedVersion(
                suggest_normalized_version(version_obj.slug)
            )
        else:
            ver = NormalizedVersion(
                suggest_normalized_version(version_obj['slug'])
            )
        return ver
    except TypeError:
        return None


def highest_version(version_list):
    highest = [None, None]
    for version in version_list:
        ver = mkversion(version)
        if not ver:
            continue
        elif highest[1] and ver:
            # If there's a highest, and no version, we don't need to set
            # anything
            if ver > highest[1]:
                highest = [version, ver]
        else:
            highest = [version, ver]
    return highest


def purge_version(version, mainsite=False, subdomain=False, cname=False):
    varnish_servers = getattr(settings, 'VARNISH_SERVERS', None)
    h = Http()
    if varnish_servers:
        for server in varnish_servers:
            if subdomain:
                #Send a request to the Server, to purge the URL of the Host.
                host = "%s.readthedocs.org" % version.project.slug
                headers = {'Host': host}
                url = "/en/%s/*" % version.slug
                to_purge = "http://%s%s" % (server, url)
                log.info("Purging %s on %s" % (url, host))
                h.request(to_purge, method="PURGE", headers=headers)
            if mainsite:
                headers = {'Host': "readthedocs.org"}
                url = "/docs/%s/en/%s/*" % (version.project.slug, version.slug)
                to_purge = "http://%s%s" % (server, url)
                log.info("Purging %s on readthedocs.org" % url)
                h.request(to_purge, method="PURGE", headers=headers)
                root_url = "/docs/%s/" % version.project.slug
                to_purge = "http://%s%s" % (server, root_url)
                log.info("Purging %s on readthedocs.org" % root_url)
                h.request(to_purge, method="PURGE", headers=headers)
            if cname:
                redis_conn = redis.Redis(**settings.REDIS)
                for cnamed in redis_conn.smembers('rtd_slug:v1:%s'
                                                  % version.project.slug):
                    headers = {'Host': cnamed}
                    url = "/en/%s/*" % version.slug
                    to_purge = "http://%s%s" % (server, url)
                    log.info("Purging %s on %s" % (url, cnamed))
                    h.request(to_purge, method="PURGE", headers=headers)
                    root_url = "/"
                    to_purge = "http://%s%s" % (server, root_url)
                    log.info("Purging %s on %s" % (root_url, cnamed))
                    h.request(to_purge, method="PURGE", headers=headers)


class DictObj(object):
    def __getattr__(self, attr):
        return self.__dict__.get(attr)

# Prevent saving the temporary Project instance
def _new_save(*args, **kwargs):
    log.warning("Called save on a non-real object.")
    return 0

def make_api_version(version_data):
    from builds.models import Version
    del version_data['resource_uri']
    project_data = version_data['project']
    project = make_api_project(project_data)
    version_data['project'] = project
    ver = Version(**version_data)
    ver.save = _new_save

    return ver


def make_api_project(project_data):
    from projects.models import Project
    for key in ['users', 'resource_uri', 'absolute_url', 'downloads']:
        if key in project_data:
            del project_data[key]
    project = Project(**project_data)
    project.save = _new_save
    return project
