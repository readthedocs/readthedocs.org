import fnmatch
import hashlib
import logging
import os

from readthedocs.core.resolver import resolve_path
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.projects.models import HTMLFile, Project, ImportedFile
from readthedocs.projects.signals import (
    bulk_post_create, 
    bulk_post_delete,
    files_changed
)
from readthedocs.worker import app

from .models import Version


log = logging.getLogger(__name__)


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return
    project = version.project

    if not commit:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg=(
                    'Imported File not being built because no commit '
                    'information'
                ),
            ),
        )
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(
            LOG_TEMPLATE.format(
                project=version.project.slug,
                version=version.slug,
                msg='Creating ImportedFiles',
            ),
        )
        _manage_imported_files(version, path, commit)
    else:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg='No ImportedFile files',
            ),
        )


def _manage_imported_files(version, path, commit):
    """
    Update imported files for version.

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    changed_files = set()
    created_html_files = []
    for root, __, filenames in os.walk(path):
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.html'):
                model_class = HTMLFile
            else:
                model_class = ImportedFile

            dirpath = os.path.join(
                root.replace(path, '').lstrip('/'), filename.lstrip('/')
            )
            full_path = os.path.join(root, filename)
            md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            try:
                # pylint: disable=unpacking-non-sequence
                obj, __ = model_class.objects.get_or_create(
                    project=version.project,
                    version=version,
                    path=dirpath,
                    name=filename,
                )
            except model_class.MultipleObjectsReturned:
                log.warning('Error creating ImportedFile')
                continue
            if obj.md5 != md5:
                obj.md5 = md5
                changed_files.add(dirpath)
            if obj.commit != commit:
                obj.commit = commit
            obj.save()

            if model_class == HTMLFile:
                # the `obj` is HTMLFile, so add it to the list
                created_html_files.append(obj)

    # Send bulk_post_create signal for bulk indexing to Elasticsearch
    bulk_post_create.send(sender=HTMLFile, instance_list=created_html_files)

    # Delete the HTMLFile first from previous commit and
    # send bulk_post_delete signal for bulk removing from Elasticsearch
    delete_queryset = (
        HTMLFile.objects.filter(project=version.project,
                                version=version).exclude(commit=commit)
    )
    # Keep the objects into memory to send it to signal
    instance_list = list(delete_queryset)
    # Safely delete from database
    delete_queryset.delete()
    # Always pass the list of instance, not queryset.
    bulk_post_delete.send(sender=HTMLFile, instance_list=instance_list)

    # Delete ImportedFiles from previous versions
    (
        ImportedFile.objects.filter(project=version.project,
                                    version=version).exclude(commit=commit
                                                             ).delete()
    )
    changed_files = [
        resolve_path(
            version.project,
            filename=file,
            version_slug=version.slug,
        ) for file in changed_files
    ]
    files_changed.send(
        sender=Project,
        project=version.project,
        files=changed_files,
    )