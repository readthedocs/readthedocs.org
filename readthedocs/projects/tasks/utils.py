import base64
import datetime
import json
import os
import shutil

import redis
import structlog
from celery.worker.request import Request
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL
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


@app.task(queue="web")
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if all the followings are true:

    - it's not in ``FINISHED`` state
    - it was created +15 minutes ago
    - there is not task queued for it on redis
    - celery is not currently executing it

    These inactive builds will be marked as ``success=False`` and ``FINISHED`` with an
    ``error`` to communicate this problem to the user.
    """
    time_limit = 15 * 60  # 15 minutes
    delta = datetime.timedelta(seconds=time_limit)
    query = (
        ~Q(state=BUILD_STATE_FINISHED) & Q(date__lte=timezone.now() - delta)
    )

    stale_build_pks = []
    builds = Build.objects.filter(query)[:50]
    redis_client = redis.Redis.from_url(settings.BROKER_URL)

    log.info("Builds not yet finished to check for stale.", count=builds.count())
    for build in builds:
        build_stale = True

        # 1. check if it's being executed by celery
        #
        # Ask Celery for all the tasks their workers are running and filter
        # them by `update_docs_task` only. Over those tasks we check if the
        # argument `build_pk` is the same than the build object we are
        # checking. In case it matches, we mark the build as NOT stale.
        tasks_running = app.control.inspect().active().items()
        log.debug(
            "Celery active tasks running.",
            tasks=tasks_running,
        )
        for queue, tasks in tasks_running:
            for task in tasks:
                try:
                    if (
                        task.get("name")
                        != "readthedocs.projects.tasks.builds.update_docs_task"
                    ):
                        log.debug(
                            "Skipping not build task. task=%s",
                            task.get("name"),
                        )
                        continue

                    task_build_pk = task.get("kwargs", {}).get("build_id")
                    log.info(
                        "Task running.",
                        task=task.get("name"),
                        build_id=task_build_pk,
                    )

                    if task_build_pk == build.pk:
                        # The build is not stale, it's being executed
                        log.info(
                            "Build not stale. Found as an active task on Celery.",
                            build_id=build.pk,
                        )
                        build_stale = False
                        break
                except Exception:
                    log.exception(
                        "There was an error accesssing the Celery task inspect."
                    )

            if not build_stale:
                # Continue with the following build that matches the filter
                break

        # 2. check if it's queued on redis
        #
        # Ask Redis for all the queues starting with `build*` (build:default,
        # build:large). Then, we check if `build_id` queued matches with the
        # build object we are checking. In that case we mark the build as NOT
        # stale.
        for queue in redis_client.keys("build*"):
            log.debug("Redis queue with queued tasks.", queue=queue)
            for task in redis_client.lrange(queue, 0, -1):
                try:
                    task = json.loads(task)
                    body = json.loads(base64.b64decode(task["body"]))
                    # ``body`` is a 3-element list
                    # [
                    #  [int],
                    #  {'record': bool, 'force': bool, 'commit': None, 'build_id': int},
                    #  {'callbacks': None, 'errbacks': None, 'chain': None, 'chord': None},
                    # ]
                    log.debug("Redis queue task.", queue=queue, body=body)

                    build_pk = body[1]["build_id"]
                    if build_pk == build.pk:
                        # The build is not stale, it's queued to be executed
                        log.info(
                            "Build not stale. Found as a queued task in Redis.",
                            build_id=build.pk,
                        )
                        build_stale = False
                        break
                except Exception:
                    log.exception(
                        "There was an error accesssing the Celery task from Redis."
                    )

            if not build_stale:
                # Continue with the following build that matches the filter
                break

        if build_stale:
            stale_build_pks.append(build.pk)

    for build_pk in stale_build_pks:
        build = Build.objects.get(pk=build_pk)
        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({}).'.format(build.pk),
        )
        build.save()

    log.warning(
        'Builds marked as "Terminated due inactivity".',
        count=len(stale_build_pks),
        build_ids=stale_build_pks,
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
