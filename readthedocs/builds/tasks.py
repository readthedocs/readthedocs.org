import json
import logging
from datetime import datetime, timedelta
from io import BytesIO

from celery import Task
from django.conf import settings
from django.core.files.storage import get_storage_class

from readthedocs.api.v2.serializers import BuildSerializer
from readthedocs.builds.constants import MAX_BUILD_COMMAND_SIZE
from readthedocs.builds.models import Build, Version
from readthedocs.builds.utils import memcache_lock
from readthedocs.worker import app

log = logging.getLogger(__name__)


class TaskRouter:

    """
    Celery tasks router.

    It allows us to decide which queue is where we want to execute the task
    based on project's settings but also in queue availability.

    1. the project is using conda
    2. new project with less than N successful builds

    It ignores projects that have already set ``build_queue`` attribute.

    https://docs.celeryproject.org/en/stable/userguide/routing.html#manual-routing
    https://docs.celeryproject.org/en/stable/userguide/configuration.html#std:setting-task_routes
    """

    N_BUILDS = 5
    N_LAST_BUILDS = 15
    TIME_AVERAGE = 350

    BUILD_DEFAULT_QUEUE = 'build:default'
    BUILD_LARGE_QUEUE = 'build:large'

    def route_for_task(self, task, args, kwargs, **__):
        log.info('Executing TaskRouter. task=%s', task)
        if task not in (
            'readthedocs.projects.tasks.update_docs_task',
            'readthedocs.projects.tasks.sync_repository_task',
        ):
            log.info('Skipping routing non-build task. task=%s', task)
            return

        version = self._get_version(task, args, kwargs)
        if not version:
            log.info('No Build/Version found. No routing task. task=%s', task)
            return

        project = version.project

        # Do not override the queue defined in the project itself
        if project.build_queue:
            log.info(
                'Skipping routing task because project has a custom queue. project=%s queue=%s',
                project.slug, project.build_queue,
            )
            return project.build_queue

        queryset = version.builds.filter(success=True).order_by('-date')
        last_builds = queryset[:self.N_LAST_BUILDS]

        # Version has used conda in previous builds
        for build in last_builds.iterator():
            if build.config.get('conda', None):
                log.info(
                    'Routing task because project uses conda. project=%s queue=%s',
                    project.slug, self.BUILD_LARGE_QUEUE,
                )
                return self.BUILD_LARGE_QUEUE

        # We do not have enough builds for this version yet
        if queryset.count() < self.N_BUILDS:
            log.info(
                'Routing task because it does not have enough success builds yet. '
                'project=%s queue=%s',
                project.slug, self.BUILD_LARGE_QUEUE,
            )
            return self.BUILD_LARGE_QUEUE

        log.info('No routing task because no conditions were met. project=%s', project.slug)
        return

    def _get_version(self, task, args, kwargs):
        tasks = [
            'readthedocs.projects.tasks.update_docs_task',
            'readthedocs.projects.tasks.sync_repository_task',
        ]
        version = None
        if task in tasks:
            version_pk = args[0]
            try:
                version = Version.objects.get(pk=version_pk)
            except Version.DoesNotExist:
                log.info(
                    'Version does not exist. Routing task to default queue. version_pk=%s',
                    version_pk,
                )
        return version


class ArchiveBuilds(Task):

    """Task to archive old builds to cold storage."""

    name = __name__ + '.archive_builds'

    def run(self, *args, **kwargs):
        if not settings.RTD_SAVE_BUILD_COMMANDS_TO_STORAGE:
            return

        lock_id = '{0}-lock'.format(self.name)
        days = kwargs.get('days', 14)
        limit = kwargs.get('limit', 5000)
        delete = kwargs.get('delete', True)

        with memcache_lock(lock_id, self.app.oid) as acquired:
            if acquired:
                archive_builds_task(days=days, limit=limit, delete=delete)
            else:
                log.warning('Archive Builds Task still locked')


def archive_builds_task(days=14, limit=200, include_cold=False, delete=False):
    """
    Find stale builds and remove build paths.

    :arg days: Find builds older than `days` days.
    :arg include_cold: If True, include builds that are already in cold storage
    :arg delete: If True, deletes BuildCommand objects after archiving them
    """
    max_date = datetime.now() - timedelta(days=days)
    queryset = Build.objects.exclude(commands__isnull=True)
    if not include_cold:
        queryset = queryset.exclude(cold_storage=True)
    queryset = queryset.filter(date__lt=max_date)[:limit]

    storage = get_storage_class(settings.RTD_BUILD_COMMANDS_STORAGE)()
    for build in queryset:
        data = BuildSerializer(build).data['commands']
        if data:
            for cmd in data:
                if len(cmd['output']) > MAX_BUILD_COMMAND_SIZE:
                    cmd['output'] = cmd['output'][:MAX_BUILD_COMMAND_SIZE]
                    cmd['output'] += "\n\nCommand output too long. Truncated at 1MB."
                    log.warning('Truncating build command for build %s', build.pk)
            output = BytesIO()
            output.write(json.dumps(data).encode('utf8'))
            output.seek(0)
            filename = '{date}/{id}.json'.format(date=str(build.date.date()), id=build.id)
            try:
                storage.save(name=filename, content=output)
                build.cold_storage = True
                build.save()
                if delete:
                    build.commands.all().delete()
            except IOError:
                log.exception('Cold Storage save failure')
