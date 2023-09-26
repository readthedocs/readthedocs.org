from fnmatch import fnmatch

import structlog

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.projects.signals import files_changed
from readthedocs.search.documents import PageDocument
from readthedocs.search.utils import index_objects, remove_indexed_files
from readthedocs.storage import build_media_storage
from readthedocs.worker import app

log = structlog.get_logger(__name__)


@app.task(queue="reindex")
def index_build(build_id):
    """Create imported files and search index for the build."""
    build = (
        Build.objects.filter(pk=build_id)
        .select_related("version", "version__project")
        .first()
    )
    if not build:
        log.debug(
            "Skipping search indexing. Build object doesn't exists.", build_id=build_id
        )
        return

    # The version may have been deleted.
    version = build.version
    if not version:
        log.debug(
            "Skipping search indexing. Build doesn't have a version attach it to it.",
            build_id=build_id,
        )
        return

    log.bind(
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=build.id,
    )

    build_config = build.config or {}
    search_config = build_config.get("search", {})
    search_ranking = search_config.get("ranking", [])
    search_ignore = search_config.get("ignore", [])

    try:
        _create_imported_files_and_search_index(
            version=version,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )
    except Exception:
        log.exception("Failed during creation of new files")


@app.task(queue="reindex")
def reindex_version(version_id, search_index_name=None):
    """
    Re-create imported files and search index for the version.

    The latest successful build is used for the re-creation.
    """
    version = Version.objects.filter(pk=version_id).select_related("project").first()
    if not version or not version.built:
        log.debug(
            "Skipping search indexing. Version doesn't exist or is not built.",
            version_id=version_id,
        )
        return

    latest_successful_build = (
        version.builds.filter(state=BUILD_STATE_FINISHED, success=True)
        .order_by("-date")
        .first()
    )
    # If the version doesn't have a successful
    # build, we don't have files to index.
    if not latest_successful_build:
        log.debug(
            "Skipping search indexing. Version doesn't have a successful build.",
            version_id=version_id,
        )
        return

    log.bind(
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=latest_successful_build.id,
    )

    build_config = latest_successful_build.config or {}
    search_config = build_config.get("search", {})
    search_ranking = search_config.get("ranking", [])
    search_ignore = search_config.get("ignore", [])

    try:
        _create_imported_files_and_search_index(
            version=version,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
            search_index_name=search_index_name,
        )
    except Exception:
        log.exception("Failed during creation of new files")


@app.task(queue="web")
def remove_search_indexes(project_slug, version_slug=None):
    """Wrapper around ``remove_indexed_files`` to make it a task."""
    remove_indexed_files(
        project_slug=project_slug,
        version_slug=version_slug,
    )


def _create_imported_files_and_search_index(
    *, version, search_ranking, search_ignore, search_index_name=None
):
    """
    Create imported files and search index for the build of the version.

    If the version is external, we don't create a search index for it, only imported files.
    After the process is completed, we delete the files and search index that
    don't belong to the current build id.

    :param search_index: If provided, it will be used as the search index name,
     otherwise the default one will be used.
    """
    storage_path = version.project.get_storage_path(
        type_="html",
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    # A sync ID is a number different than the current `build` attribute (pending rename),
    # it's used to differentiate the files from the current sync from the previous one.
    # This is useful to easily delete the previous files from the DB and ES.
    # See https://github.com/readthedocs/readthedocs.org/issues/10734.
    imported_file = version.imported_files.first()
    sync_id = imported_file.build + 1 if imported_file else 1

    log.debug(
        "Using sync ID for search indexing",
        sync_id=sync_id,
    )

    html_files_to_index = []
    html_files_to_save = []
    reverse_rankings = list(reversed(search_ranking.items()))
    for root, __, filenames in build_media_storage.walk(storage_path):
        for filename in filenames:
            # We don't care about non-HTML files
            if not filename.endswith(".html"):
                continue

            full_path = build_media_storage.join(root, filename)

            # Generate a relative path for storage similar to os.path.relpath
            relpath = full_path.replace(storage_path, "", 1).lstrip("/")

            skip_search_index = False
            if version.is_external:
                # Never index files from external versions.
                skip_search_index = True
            else:
                for pattern in search_ignore:
                    if fnmatch(relpath, pattern):
                        skip_search_index = True
                        break

            page_rank = 0
            # If the file is ignored, we don't need to check for its ranking.
            if not skip_search_index:
                # Last pattern to match takes precedence
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
                # TODO: We are setting the commit field since it's required,
                # but it isn't used, and will be removed in the future
                # together with other fields.
                commit="unknown",
                build=sync_id,
                ignore=skip_search_index,
            )

            if not skip_search_index:
                html_files_to_index.append(html_file)

            # Create the imported file only if it's a top-level 404 file,
            # or if it's an index file. We don't need to keep track of all files.
            if relpath == "404.html" or filename in ["index.html", "README.html"]:
                html_files_to_save.append(html_file)

    # We first index the files in ES, and then save the objects in the DB.
    # This is because saving the objects in the DB will give them an id,
    # and we neeed this id to be `None` when indexing the objects in ES.
    # ES will generate a unique id for each document.
    if html_files_to_index:
        index_objects(
            document=PageDocument,
            objects=html_files_to_index,
            index_name=search_index_name,
        )

    # Remove old HTMLFiles from ElasticSearch
    remove_indexed_files(
        project_slug=version.project.slug,
        version_slug=version.slug,
        sync_id=sync_id,
        index_name=search_index_name,
    )

    if html_files_to_save:
        HTMLFile.objects.bulk_create(html_files_to_save)

    # Delete imported files from the previous build of the version.
    version.imported_files.exclude(build=sync_id).delete()

    # This signal is used for purging the CDN.
    files_changed.send(
        sender=Project,
        project=version.project,
        version=version,
    )
    return sync_id
