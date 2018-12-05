# -*- coding: utf-8 -*-
"""Utility functions used by projects."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
import os

from builtins import open
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
