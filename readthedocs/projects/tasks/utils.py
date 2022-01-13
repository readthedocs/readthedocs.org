import datetime
import json
import os
import shutil

from fnmatch import fnmatch

import structlog
from sphinx.ext import intersphinx

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.builds.tasks import send_build_status
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.signals import files_changed
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.storage import build_media_storage
from readthedocs.vcs_support.utils import LockTimeout
from readthedocs.worker import app

from .mixins import SyncRepositoryMixin


log = structlog.get_logger(__name__)


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


def clean_build(version_pk):
    """Clean the files used in the build of the given version."""
    try:
        version = SyncRepositoryMixin.get_version(version_pk)
    except Exception:
        log.exception('Error while fetching the version from the api')
        return False
    if (
        not settings.RTD_CLEAN_AFTER_BUILD and
        not version.project.has_feature(Feature.CLEAN_AFTER_BUILD)
    ):
        log.info(
            'Skipping build files deletetion for version.',
            version_id=version_pk,
        )
        return False
    # NOTE: we are skipping the deletion of the `artifacts` dir
    # because we are syncing the servers with an async task.
    del_dirs = [
        os.path.join(version.project.doc_path, dir_, version.slug)
        for dir_ in ('checkouts', 'envs', 'conda')
    ]
    del_dirs.append(
        os.path.join(version.project.doc_path, '.cache')
    )
    try:
        with version.project.repo_nonblockinglock(version):
            log.info('Removing directories.', directories=del_dirs)
            remove_dirs(del_dirs)
    except LockTimeout:
        log.info('Another task is running. Not removing...', directories=del_dirs)
    else:
        return True


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


@app.task()
def remove_dirs(paths):
    """
    Remove artifacts from servers.

    This is mainly a wrapper around shutil.rmtree so that we can remove things across
    every instance of a type of server (eg. all builds or all webs).

    :param paths: list containing PATHs where file is on disk
    """
    for path in paths:
        log.info('Removing directory.', path=path)
        shutil.rmtree(path, ignore_errors=True)


@app.task(queue='web')
def remove_build_storage_paths(paths):
    """
    Remove artifacts from build media storage (cloud or local storage).

    :param paths: list of paths in build media storage to delete
    """
    for storage_path in paths:
        log.info('Removing path from media storage.', path=storage_path)
        build_media_storage.delete_directory(storage_path)


def clean_project_resources(project, version=None):
    """
    Delete all extra resources used by `version` of `project`.

    It removes:

    - Artifacts from storage.
    - Search indexes from ES.

    :param version: Version instance. If isn't given,
                    all resources of `project` will be deleted.

    .. note::
       This function is usually called just before deleting project.
       Make sure to not depend on the project object inside the tasks.
    """
    # Remove storage paths
    storage_paths = []
    if version:
        storage_paths = version.get_storage_paths()
    else:
        storage_paths = project.get_storage_paths()
    remove_build_storage_paths.delay(storage_paths)

    # Remove indexes
    from .search import remove_search_indexes  # noqa
    remove_search_indexes.delay(
        project_slug=project.slug,
        version_slug=version.slug if version else None,
    )


@app.task()
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if it's not in ``FINISHED`` state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``FINISHED`` with an
    ``error`` to be communicated to the user.
    """
    # TODO similar to the celery task time limit, we can't infer this from
    # Docker settings anymore, because Docker settings are determined on the
    # build servers dynamically.
    # time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    # Set time as maximum celery task time limit + 5m
    time_limit = 7200 + 300
    delta = datetime.timedelta(seconds=time_limit)
    query = (
        ~Q(state=BUILD_STATE_FINISHED) & Q(date__lte=timezone.now() - delta)
    )

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as FINISHED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({}).'.format(build.pk),
        )
        build.save()
        builds_finished += 1

    log.info(
        'Builds marked as "Terminated due inactivity".',
        count=builds_finished,
    )


def send_external_build_status(version_type, build_pk, commit, status):
    """
    Check if build is external and Send Build Status for project external versions.

     :param version_type: Version type e.g EXTERNAL, BRANCH, TAG
     :param build_pk: Build pk
     :param commit: commit sha of the pull/merge request
     :param status: build status failed, pending, or success to be sent.
    """

    # Send status reports for only External (pull/merge request) Versions.
    if version_type == EXTERNAL:
        # call the task that actually send the build status.
        send_build_status.delay(build_pk, commit, status)
