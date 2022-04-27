import datetime
import os
import shutil

import structlog
from celery.worker.request import Request
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import BUILD_FINAL_STATES, EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.builds.tasks import send_build_status
from readthedocs.storage import build_media_storage
from readthedocs.worker import app

log = structlog.get_logger(__name__)


def clean_build(version):
    """Clean the files used in the build of the given version."""
    del_dirs = [
        os.path.join(version.project.doc_path, dir_, version.slug)
        for dir_ in ('checkouts', 'envs', 'conda', 'artifacts')
    ]
    del_dirs.append(
        os.path.join(version.project.doc_path, '.cache')
    )

    log.info('Removing directories.', directories=del_dirs)
    for path in del_dirs:
        shutil.rmtree(path, ignore_errors=True)


@app.task(queue='web')
def remove_build_storage_paths(paths):
    """
    Remove artifacts from build media storage (cloud or local storage).

    :param paths: list of paths in build media storage to delete
    """
    log.info('Removing path from media storage.', paths=paths)
    for storage_path in paths:
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

    A build is consider inactive if it's not in a final state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``CANCELLED`` with an
    ``error`` to be communicated to the user.
    """
    # TODO similar to the celery task time limit, we can't infer this from
    # Docker settings anymore, because Docker settings are determined on the
    # build servers dynamically.
    # time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    # Set time as maximum celery task time limit + 5m
    time_limit = 7200 + 300
    delta = datetime.timedelta(seconds=time_limit)
    query = ~Q(state__in=BUILD_FINAL_STATES) & Q(date__lte=timezone.now() - delta)

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as CANCELLED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_CANCELLED
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


class BuildRequest(Request):

    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)

        log.bind(
            task_name=self.task.name,
            project_slug=self.task.data.project.slug,
            build_id=self.task.data.build['id'],
            timeout=timeout,
            soft=soft,
        )
        if soft:
            log.warning('Build is taking too much time. Risk to be killed soon.')
        else:
            log.warning('A timeout was enforced for task.')
