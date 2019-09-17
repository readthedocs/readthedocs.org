# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.shortcuts import get_object_or_404

from readthedocs.core.utils import broadcast
from readthedocs.projects.tasks import remove_dirs
from readthedocs.builds.models import Version
from readthedocs.projects.tasks import remove_build_storage_paths


def wipe_version_via_slugs(version_slug, project_slug):
    """
    Wipes the given version of a project.

    It does two things:
    * Clears the `checkouts`, `envs`, and `conda` direcories (if exist).
    * Removes the html files from cloud storage.
    """
    version = get_object_or_404(
        Version,
        slug=version_slug,
        project__slug=project_slug,
    )
    del_dirs = [
        os.path.join(version.project.doc_path, 'checkouts', version.slug),
        os.path.join(version.project.doc_path, 'envs', version.slug),
        os.path.join(version.project.doc_path, 'conda', version.slug),
    ]
    for del_dir in del_dirs:
        broadcast(type='build', task=remove_dirs, args=[(del_dir,)])

    _clear_html_files_from_cloud_storage(version)


def _clear_html_files_from_cloud_storage(version):
    """Removes html files from media storage (cloud or local) for a given version of a project."""

    storage_path = version.project.get_storage_path(
        type_='html',
        version_slug=version.slug,
        include_file=False,
    )
    remove_build_storage_paths.delay([storage_path])
