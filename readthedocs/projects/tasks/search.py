import structlog

from readthedocs.worker import app

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, ImportedFile
from readthedocs.search.utils import remove_indexed_files, index_new_files
from readthedocs.sphinx_domains.models import SphinxDomain

from .utils import _create_imported_files, _create_intersphinx_data

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
            build=build,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )
    except Exception:
        log.exception('Failed during ImportedFile creation')

    try:
        _create_intersphinx_data(version, commit, build)
    except Exception:
        log.exception('Failed during SphinxDomain creation')

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

    # Index new HTMLFiles to ElasticSearch
    index_new_files(model=HTMLFile, version=version, build=build)

    # Remove old HTMLFiles from ElasticSearch
    remove_indexed_files(
        model=HTMLFile,
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=build,
    )

    # Delete SphinxDomain objects from previous versions
    # This has to be done before deleting ImportedFiles and not with a cascade,
    # because multiple Domain's can reference a specific HTMLFile.
    (
        SphinxDomain.objects
        .filter(project=version.project, version=version)
        .exclude(build=build)
        .delete()
    )

    # Delete ImportedFiles objects (including HTMLFiles)
    # from the previous build of the version.
    (
        ImportedFile.objects
        .filter(project=version.project, version=version)
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
