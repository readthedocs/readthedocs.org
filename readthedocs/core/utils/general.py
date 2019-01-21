# -*- coding: utf-8 -*-

from __future__ import (
    division,
    print_function,
    unicode_literals,
)

import os

from django.shortcuts import get_object_or_404

from readthedocs.core.utils import broadcast
from readthedocs.projects.tasks import remove_dirs
from readthedocs.builds.models import Version


def wipe_version_via_slug(version_slug):
    """Wipes the given version."""
    version = get_object_or_404(Version, slug=version_slug)
    del_dirs = [
        os.path.join(version.project.doc_path, 'checkouts', version.slug),
        os.path.join(version.project.doc_path, 'envs', version.slug),
        os.path.join(version.project.doc_path, 'conda', version.slug),
    ]
    for del_dir in del_dirs:
        broadcast(type='build', task=remove_dirs, args=[(del_dir,)])
