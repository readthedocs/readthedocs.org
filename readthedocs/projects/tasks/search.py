from fnmatch import fnmatch

import structlog
from django.conf import settings

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.builds.tasks import post_build_overview
from readthedocs.filetreediff import write_manifest
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifestFile
from readthedocs.projects.models import HTMLFile
from readthedocs.projects.models import Project
from readthedocs.projects.signals import files_changed
from readthedocs.search.documents import PageDocument
from readthedocs.search.utils import index_objects
from readthedocs.search.utils import remove_indexed_files
from readthedocs.storage import build_media_storage
from readthedocs.worker import app


log = structlog.get_logger(__name__)


class Indexer:
    """
    Base class for doing operations over each file from a build.

    The process method should be implemented to apply the operation
    over each file, and the collect method should be implemented
    to collect the results of the operation after processing all files.

    `sync_id` is used to differentiate the files from the current sync from the previous one.
    """

    def process(self, html_file: HTMLFile, sync_id: int):
        raise NotImplementedError

    def collect(self, sync_id: int):
        raise NotImplementedError


class SearchIndexer(Indexer):
    """
    Index HTML files in ElasticSearch.

    We respect the search ranking and ignore patterns defined in the project's search configuration.

    If search_index_name is provided, it will be used as the search index name,
    otherwise the default one will be used.
    """

    def __init__(
        self,
        project: Project,
        version: Version,
        search_ranking: dict[str, int],
        search_ignore: list[str],
        search_index_name: str | None = None,
    ):
        self.project = project
        self.version = version
        self.search_ranking = search_ranking
        self.search_ignore = search_ignore
        self._reversed_search_ranking = list(reversed(search_ranking.items()))
        self.search_index_name = search_index_name
        self._html_files_to_index = []

    def process(self, html_file: HTMLFile, sync_id: int):
        for pattern in self.search_ignore:
            if fnmatch(html_file.path, pattern):
                return

        for pattern, rank in self._reversed_search_ranking:
            if fnmatch(html_file.path, pattern):
                html_file.rank = rank
                break

        self._html_files_to_index.append(html_file)

    def collect(self, sync_id: int):
        # Index new files in ElasticSearch.
        if self._html_files_to_index:
            index_objects(
                document=PageDocument,
                objects=self._html_files_to_index,
                index_name=self.search_index_name,
                # Pages are indexed in small chunks to avoid a
                # large payload that will probably timeout ES.
                chunk_size=100,
            )

        # Remove old HTMLFiles from ElasticSearch.
        remove_indexed_files(
            project_slug=self.project.slug,
            version_slug=self.version.slug,
            sync_id=sync_id,
            index_name=self.search_index_name,
        )


class IndexFileIndexer(Indexer):
    """
    Create imported files of interest in the DB.

    We only save the top-level 404 file and index files,
    we don't need to keep track of all files.
    These files are queried by proxito instead of checking S3 (slow).
    """

    def __init__(self, project: Project, version: Version):
        self.project = project
        self.version = version
        self._html_files_to_save = []

    def process(self, html_file: HTMLFile, sync_id: int):
        if html_file.path == "404.html" or html_file.name == "index.html":
            self._html_files_to_save.append(html_file)

    def collect(self, sync_id: int):
        if self._html_files_to_save:
            HTMLFile.objects.bulk_create(self._html_files_to_save)

        # Delete imported files from the previous build of the version.
        self.version.imported_files.exclude(build=sync_id).delete()


class FileManifestIndexer(Indexer):
    def __init__(self, version: Version, build: Build):
        self.version = version
        self.build = build
        self._hashes = {}

    def process(self, html_file: HTMLFile, sync_id: int):
        self._hashes[html_file.path] = html_file.processed_json["main_content_hash"]

    def collect(self, sync_id: int):
        manifest = FileTreeDiffManifest(
            build_id=self.build.id,
            files=[
                FileTreeDiffManifestFile(path=path, main_content_hash=hash)
                for path, hash in self._hashes.items()
            ],
        )
        write_manifest(self.version, manifest)
        if self.version.is_external and self.version.project.show_build_overview_in_comment:
            post_build_overview.delay(self.build.id)


def _get_indexers(*, version: Version, build: Build, search_index_name=None):
    build_config = build.config or {}
    search_config = build_config.get("search", {})
    search_ranking = search_config.get("ranking", {})
    search_ignore = search_config.get("ignore", [])

    indexers = []
    # NOTE: The search indexer must be before the index file indexer.
    # This is because saving the objects in the DB will give them an id,
    # and we neeed this id to be `None` when indexing the objects in ES.
    # ES will generate a unique id for each document.
    # NOTE: We don't create a search indexer for:
    # - External versions
    # - Versions from projects with search indexing disabled
    # - Versions from delisted projects
    skip_search_indexing = (
        not version.project.search_indexing_enabled
        or version.is_external
        or version.project.delisted
    )
    if not skip_search_indexing:
        search_indexer = SearchIndexer(
            project=version.project,
            version=version,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
            search_index_name=search_index_name,
        )
        indexers.append(search_indexer)

    # File tree diff is under a feature flag for now,
    # and we only allow to compare PR previews against the latest version.
    base_version = (
        version.project.addons.options_base_version.slug
        if version.project.addons.options_base_version
        else LATEST
    )
    create_manifest = version.project.addons.filetreediff_enabled and (
        version.is_external or version.slug == base_version or settings.RTD_FILETREEDIFF_ALL
    )
    if create_manifest:
        file_manifest_indexer = FileManifestIndexer(
            version=version,
            build=build,
        )
        indexers.append(file_manifest_indexer)

    index_file_indexer = IndexFileIndexer(
        project=version.project,
        version=version,
    )
    indexers.append(index_file_indexer)
    return indexers


def _process_files(*, version: Version, indexers: list[Indexer]):
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
    imported_file_build_id = version.imported_files.values_list("build", flat=True).first()
    sync_id = imported_file_build_id + 1 if imported_file_build_id else 1

    log.debug(
        "Using sync ID for search indexing",
        sync_id=sync_id,
    )

    for root, __, filenames in build_media_storage.walk(storage_path):
        for filename in filenames:
            # We don't care about non-HTML files (for now?).
            if not filename.endswith(".html"):
                continue

            full_path = build_media_storage.join(root, filename)
            # Generate a relative path for storage similar to os.path.relpath
            relpath = full_path.removeprefix(storage_path).lstrip("/")

            html_file = HTMLFile(
                project=version.project,
                version=version,
                path=relpath,
                name=filename,
                # TODO: We are setting the commit field since it's required,
                # but it isn't used, and will be removed in the future
                # together with other fields.
                commit="unknown",
                build=sync_id,
            )
            for indexer in indexers:
                try:
                    indexer.process(html_file, sync_id)
                except Exception:
                    log.exception(
                        "Failed to process HTML file",
                        html_file=html_file.path,
                        indexer=indexer.__class__.__name__,
                        version_slug=version.slug,
                    )

    for indexer in indexers:
        try:
            indexer.collect(sync_id)
        except Exception:
            log.exception(
                "Failed to collect indexer results",
                indexer=indexer.__class__.__name__,
                version_slug=version.slug,
            )

    # This signal is used for purging the CDN.
    files_changed.send(
        sender=Project,
        project=version.project,
        version=version,
    )
    return sync_id


@app.task(queue="reindex")
def index_build(build_id):
    """Create imported files and search index for the build."""
    build = Build.objects.filter(pk=build_id).select_related("version", "version__project").first()
    if not build:
        log.debug("Skipping search indexing. Build object doesn't exists.", build_id=build_id)
        return

    # The version may have been deleted.
    version = build.version
    if not version:
        log.debug(
            "Skipping search indexing. Build doesn't have a version attach it to it.",
            build_id=build_id,
        )
        return

    structlog.contextvars.bind_contextvars(
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=build.id,
    )

    try:
        indexers = _get_indexers(
            version=version,
            build=build,
        )
        return _process_files(version=version, indexers=indexers)
    except Exception:
        log.exception("Failed to index build")


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
        version.builds.filter(state=BUILD_STATE_FINISHED, success=True).order_by("-date").first()
    )
    # If the version doesn't have a successful
    # build, we don't have files to index.
    if not latest_successful_build:
        log.debug(
            "Skipping search indexing. Version doesn't have a successful build.",
            version_id=version_id,
        )
        return

    structlog.contextvars.bind_contextvars(
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=latest_successful_build.id,
    )
    try:
        indexers = _get_indexers(
            version=version,
            build=latest_successful_build,
            search_index_name=search_index_name,
        )
        _process_files(version=version, indexers=indexers)
    except Exception:
        log.exception("Failed to re-index version")


@app.task(queue="reindex")
def index_project(project_slug, skip_if_exists=False):
    """
    Index all active versions of the project.

    If ``skip_if_exists`` is True, we first check if
    the project has at least one version indexed,
    and skip the re-indexing if it does.
    """
    structlog.contextvars.bind_contextvars(project_slug=project_slug)
    project = Project.objects.filter(slug=project_slug).first()
    if not project:
        log.debug("Project doesn't exist.")
        return

    if skip_if_exists:
        if PageDocument().search().filter("term", project=project.slug).count():
            log.debug("Skipping search indexing. Project is already indexed.")
            return

    versions = project.versions(manager=INTERNAL).filter(active=True, built=True)
    for version in versions:
        reindex_version(version_id=version.id)


@app.task(queue="web")
def remove_search_indexes(project_slug, version_slug=None):
    """Wrapper around ``remove_indexed_files`` to make it a task."""
    remove_indexed_files(
        project_slug=project_slug,
        version_slug=version_slug,
    )
