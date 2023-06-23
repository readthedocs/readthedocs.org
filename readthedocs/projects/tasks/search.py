import os
from fnmatch import fnmatch

import structlog

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.signals import files_changed
from readthedocs.search.utils import index_new_files, remove_indexed_files
from readthedocs.storage import build_media_storage
from readthedocs.worker import app

log = structlog.get_logger(__name__)


@app.task(queue='reindex')
def fileify(version_pk, commit, build, search_ranking, search_ignore):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    # Don't index external version builds for now
    if not version or version.type == EXTERNAL:
        return
    project = version.project

    if not commit:
        log.warning(
            'Search index not being built because no commit information',
            project_slug=project.slug,
            version_slug=version.slug,
        )
        return

    log.info(
        "Creating ImportedFiles for search indexing",
        project_slug=version.project.slug,
        version_slug=version.slug,
    )
    try:
        _create_imported_files(
            version=version,
            commit=commit,
            build=build,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )
    except Exception:
        log.exception('Failed during ImportedFile creation')

    try:
        _sync_imported_files(version, build)
    except Exception:
        log.exception('Failed during ImportedFile syncing')


@app.task(queue="web")
def sync_downloadable_artifacts(
    version_pk, commit, build, artifacts_found_for_download
):
    """
    Create ImportedFile objects for downloadable files.

    Afterwards, ImportedFile objects are used to generate a list of files that can be downloaded
    for each documentation version.

    :param artifacts_found_for_download: A dictionary with a list of files for each artifact type.
      For example: {"pdf": ["path/to/file1.pdf", "path/to/file2.pdf"]}
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    log.info(
        "Creating ImportedFiles for artifact downloads",
        project_slug=version.project.slug,
        version_slug=version.slug,
        artifacts_found_for_download=artifacts_found_for_download,
    )

    # Don't index external version builds for now
    if not version or version.type == EXTERNAL:
        return

    for artifact_type, artifact_paths in artifacts_found_for_download.items():
        for fpath in artifact_paths:
            name = os.path.basename(fpath)
            ImportedFile.objects.create(
                name=name,
                project=version.project,
                version=version,
                path=fpath,
                commit=commit,
                build=build,
                ignore=True,
            )


def _sync_imported_files(version, build):
    """
    Sync/Update/Delete ImportedFiles objects of this version.

    :param version: Version instance
    :param build: Build id
    """
    project = version.project

    # Index new HTMLFiles to ElasticSearch
    index_new_files(model=HTMLFile, version=version, build=build)

    # Remove old HTMLFiles from ElasticSearch
    remove_indexed_files(
        model=HTMLFile,
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=build,
    )

    # Delete ImportedFiles objects (including HTMLFiles)
    # from the previous build of the version.
    (
        ImportedFile.objects.filter(project=project, version=version)
        .exclude(build=build)
        .delete()
    )


@app.task(queue='web')
def remove_search_indexes(project_slug, version_slug=None):
    """Wrapper around ``remove_indexed_files`` to make it a task."""
    remove_indexed_files(
        model=HTMLFile,
        project_slug=project_slug,
        version_slug=version_slug,
    )


def _create_imported_files(*, version, commit, build, search_ranking, search_ignore):
    """
    Create imported files for version.

    :param version: Version instance
    :param commit: Commit that updated path
    :param build: Build id
    """
    # Re-create all objects from the new build of the version
    storage_path = version.project.get_storage_path(
        type_='html', version_slug=version.slug, include_file=False
    )
    for root, __, filenames in build_media_storage.walk(storage_path):
        for filename in filenames:
            # We don't care about non-HTML files
            if not filename.endswith('.html'):
                continue

            full_path = build_media_storage.join(root, filename)

            # Generate a relative path for storage similar to os.path.relpath
            relpath = full_path.replace(storage_path, '', 1).lstrip('/')

            page_rank = 0
            # Last pattern to match takes precedence
            # XXX: see if we can implement another type of precedence,
            # like the longest pattern.
            reverse_rankings = reversed(list(search_ranking.items()))
            for pattern, rank in reverse_rankings:
                if fnmatch(relpath, pattern):
                    page_rank = rank
                    break

            ignore = False
            for pattern in search_ignore:
                if fnmatch(relpath, pattern):
                    ignore = True
                    break

            # Create imported files from new build
            HTMLFile.objects.create(
                project=version.project,
                version=version,
                path=relpath,
                name=filename,
                rank=page_rank,
                commit=commit,
                build=build,
                ignore=ignore,
            )

    # This signal is used for purging the CDN.
    files_changed.send(
        sender=Project,
        project=version.project,
        version=version,
    )
