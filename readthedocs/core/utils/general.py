# -*- coding: utf-8 -*-

import os

from django.shortcuts import get_object_or_404

from readthedocs.core.utils import broadcast
from readthedocs.projects.tasks import remove_dirs
from readthedocs.builds.models import Version


def wipe_version_via_slugs(version_slug, project_slug):
    """Wipes the given version of a given project."""
    version = get_object_or_404(
        Version,
        slug=version_slug,
        project__slug=project_slug
    )
    del_dirs = [
        os.path.join(version.project.doc_path, 'checkouts', version.slug),
        os.path.join(version.project.doc_path, 'envs', version.slug),
        os.path.join(version.project.doc_path, 'conda', version.slug),
    ]
    for del_dir in del_dirs:
        broadcast(type='build', task=remove_dirs, args=[(del_dir,)])
