from fnmatch import fnmatch

import structlog

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.signals import files_changed
from readthedocs.search.utils import remove_indexed_files
from django_elasticsearch_dsl.registries import registry
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
        'Creating ImportedFiles',
        project_slug=version.project.slug,
        version_slug=version.slug,
    )
    try:
        _create_imported_files(
            version=version,
            commit=commit,
            build_id=build,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )
    except Exception:
        log.exception('Failed during ImportedFile creation')

    try:
        _sync_imported_files(version, build)
    except Exception:
        log.exception('Failed during ImportedFile syncing')


def _sync_imported_files(version, build):
    """
    Sync/Update/Delete ImportedFiles objects of this version.

    :param version: Version instance
    :param build: Build id
    """
    project = version.project

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


def reindex_version(version):
    """
    Reindex all files of this version.
    """
    latest_successful_build = version.builds.filter(
        state=BUILD_STATE_FINISHED, success=True
    ).order_by("-date").first()
    # If the version doesn't have a successful
    # build, we don't have files to index.
    if not latest_successful_build:
        return

    search_ranking = []
    search_ignore = []
    build_config = latest_successful_build.config
    if build_config:
        search_ranking = build_config.search.ranking
        search_ignore = build_config.search.ignore

    _create_imported_files(
        version=version,
        commit=latest_successful_build.commit,
        build_id=latest_successful_build.id,
        search_ranking=search_ranking,
        search_ignore=search_ignore,
    )


def _create_imported_files(*, version, commit, build_id, search_ranking, search_ignore):
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
    html_files_to_index = []
    html_files_to_save = []
    reverse_rankings = reversed(list(search_ranking.items()))
    for root, __, filenames in build_media_storage.walk(storage_path):
        for filename in filenames:
            # We don't care about non-HTML files
            if not filename.endswith('.html'):
                continue

            full_path = build_media_storage.join(root, filename)

            # Generate a relative path for storage similar to os.path.relpath
            relpath = full_path.replace(storage_path, '', 1).lstrip('/')

            ignore = False
            if version.is_external:
                # Never index files from external versions.
                ignore = True
            else:
                for pattern in search_ignore:
                    if fnmatch(relpath, pattern):
                        ignore = True
                        break

            page_rank = 0
            # If the file is ignored, we don't need to check for its ranking.
            if not ignore:
                # Last pattern to match takes precedence
                # XXX: see if we can implement another type of precedence,
                # like the longest pattern.
                for pattern, rank in reverse_rankings:
                    if fnmatch(relpath, pattern):
                        page_rank = rank
                        break

            html_file = HTMLFile(
                project=version.project,
                version=version,
                path=relpath,
                name=filename,
                rank=page_rank,
                commit=commit,
                build=build_id,
                ignore=ignore,
            )

            # Don't index files that are ignored.
            if not ignore:
                html_files_to_index.append(html_file)

            # Create the imported file only if it's a top-level 404 file,
            # or if it's an index file. We don't need to keep track of all files.
            is_top_level_404_file = filename == "404.html" and root == storage_path
            is_index_file = filename in ["index.html", "README.html"]
            if is_top_level_404_file or is_index_file:
                html_files_to_save.append(html_file)

        # We first index the files in ES, and then save the objects in the DB.
        # This is because saving the objects in the DB will give them an id,
        # and we neeed this id to be `None` when indexing the objects in ES.
        # ES will generate a unique id for each document.
        if html_files_to_index:
            document = list(registry.get_documents(models=[HTMLFile]))[0]
            document().update(html_files_to_index)

        if html_files_to_save:
            HTMLFile.objects.bulk_create(html_files_to_save)

    # This signal is used for purging the CDN.
    files_changed.send(
        sender=Project,
        project=version.project,
        version=version,
    )
