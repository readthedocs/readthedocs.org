from fnmatch import fnmatch
import json

from sphinx.ext import intersphinx
import structlog

from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.signals import files_changed
from readthedocs.search.utils import remove_indexed_files, index_new_files
from readthedocs.sphinx_domains.models import SphinxDomain
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


def _create_intersphinx_data(version, commit, build):
    """
    Create intersphinx data for this version.

    :param version: Version instance
    :param commit: Commit that updated path
    :param build: Build id
    """
    if not version.is_sphinx_type:
        return

    html_storage_path = version.project.get_storage_path(
        type_='html', version_slug=version.slug, include_file=False
    )
    json_storage_path = version.project.get_storage_path(
        type_='json', version_slug=version.slug, include_file=False
    )

    object_file = build_media_storage.join(html_storage_path, 'objects.inv')
    if not build_media_storage.exists(object_file):
        log.debug('No objects.inv, skipping intersphinx indexing.')
        return

    type_file = build_media_storage.join(json_storage_path, 'readthedocs-sphinx-domain-names.json')
    types = {}
    titles = {}
    if build_media_storage.exists(type_file):
        try:
            data = json.load(build_media_storage.open(type_file))
            types = data['types']
            titles = data['titles']
        except Exception:
            log.exception('Exception parsing readthedocs-sphinx-domain-names.json')

    # These classes are copied from Sphinx
    # https://github.com/sphinx-doc/sphinx/blob/d79d041f4f90818e0b495523fdcc28db12783caf/sphinx/ext/intersphinx.py#L400-L403  # noqa
    class MockConfig:
        intersphinx_timeout = None
        tls_verify = False
        user_agent = None

    class MockApp:
        srcdir = ''
        config = MockConfig()

        def warn(self, msg):
            log.warning('Sphinx MockApp.', msg=msg)

    # Re-create all objects from the new build of the version
    object_file_url = build_media_storage.url(object_file)
    if object_file_url.startswith('/'):
        # Filesystem backed storage simply prepends MEDIA_URL to the path to get the URL
        # This can cause an issue if MEDIA_URL is not fully qualified
        object_file_url = settings.RTD_INTERSPHINX_URL + object_file_url

    invdata = intersphinx.fetch_inventory(MockApp(), '', object_file_url)
    for key, value in sorted(invdata.items() or {}):
        domain, _type = key.split(':', 1)
        for name, einfo in sorted(value.items()):
            # project, version, url, display_name
            # ('Sphinx', '1.7.9', 'faq.html#epub-faq', 'Epub info')
            try:
                url = einfo[2]
                if '#' in url:
                    doc_name, anchor = url.split(
                        '#',
                        # The anchor can contain ``#`` characters
                        maxsplit=1
                    )
                else:
                    doc_name, anchor = url, ''
                display_name = einfo[3]
            except Exception:
                log.exception(
                    'Error while getting sphinx domain information. Skipping...',
                    project_slug=version.project.slug,
                    version_slug=version.slug,
                    sphinx_domain='{domain}->{name}',
                )
                continue

            # HACK: This is done because the difference between
            # ``sphinx.builders.html.StandaloneHTMLBuilder``
            # and ``sphinx.builders.dirhtml.DirectoryHTMLBuilder``.
            # They both have different ways of generating HTML Files,
            # and therefore the doc_name generated is different.
            # More info on: http://www.sphinx-doc.org/en/master/usage/builders/index.html#builders
            # Also see issue: https://github.com/readthedocs/readthedocs.org/issues/5821
            if doc_name.endswith('/'):
                doc_name += 'index.html'

            html_file = HTMLFile.objects.filter(
                project=version.project, version=version,
                path=doc_name, build=build,
            ).first()

            if not html_file:
                log.debug(
                    'HTMLFile object not found.',
                    project_slug=version.project.slug,
                    version_slug=version.slug,
                    build_id=build,
                    doc_name=doc_name
                )

                # Don't create Sphinx Domain objects
                # if the HTMLFile object is not found.
                continue

            SphinxDomain.objects.create(
                project=version.project,
                version=version,
                html_file=html_file,
                domain=domain,
                name=name,
                display_name=display_name,
                type=_type,
                type_display=types.get(f'{domain}:{_type}', ''),
                doc_name=doc_name,
                doc_display=titles.get(doc_name, ''),
                anchor=anchor,
                commit=commit,
                build=build,
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
