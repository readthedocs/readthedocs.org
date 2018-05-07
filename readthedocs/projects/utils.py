# -*- coding: utf-8 -*-
"""Utility functions used by projects."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import fnmatch
import logging
import os
import subprocess
import traceback

import six
from builtins import object, open
from django.conf import settings

log = logging.getLogger(__name__)


# TODO make this a classmethod of Version
def version_from_slug(slug, version):
    from readthedocs.builds.models import Version, APIVersion
    from readthedocs.restapi.client import api
    if getattr(settings, 'DONT_HIT_DB', True):
        version_data = api.version().get(
            project=slug,
            slug=version,
        )['results'][0]
        v = APIVersion(**version_data)
    else:
        v = Version.objects.get(project__slug=slug, slug=version)
    return v


def find_file(filename):
    """
    Recursively find matching file from the current working path.

    :param file: Filename to match
    :returns: A list of matching filenames.
    """
    matches = []
    for root, __, filenames in os.walk('.'):
        for match in fnmatch.filter(filenames, filename):
            matches.append(os.path.join(root, match))
    return matches


def run(*commands):
    """
    Run one or more commands.

    Each argument in `commands` can be passed as a string or as a list. Passing
    as a list is the preferred method, as space escaping is more explicit and it
    avoids the need for executing anything in a shell.

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
        raise ValueError('run() requires one or more command-line strings')

    for command in commands:
        # If command is a string, split it up by spaces to pass into Popen.
        # Otherwise treat the command as an iterable.
        if isinstance(command, six.string_types):
            run_command = command.split()
        else:
            try:
                run_command = list(command)
                command = ' '.join(command)
            except TypeError:
                run_command = command
        log.debug('Running command: cwd=%s command=%s', cwd, command)
        try:
            p = subprocess.Popen(
                run_command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
            )

            out, err = p.communicate()
            ret = p.returncode
        except OSError:
            out = ''
            err = traceback.format_exc()
            ret = -1
            log.exception('Command failed')

    return (ret, out, err)


def safe_write(filename, contents):
    """
    Normalize and write to filename.

    Write ``contents`` to the given ``filename``. If the filename's
    directory does not exist, it is created. Contents are written as UTF-8,
    ignoring any characters that cannot be encoded as UTF-8.

    :param filename: Filename to write to
    :param contents: File contents to write to file
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename, 'w', encoding='utf-8', errors='ignore') as fh:
        fh.write(contents)
        fh.close()


class DictObj(object):

    def __getattr__(self, attr):
        return self.__dict__.get(attr)
