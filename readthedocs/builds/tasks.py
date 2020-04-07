import logging

from django.conf import settings
from django.db.models import Avg

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Feature

log = logging.getLogger(__name__)


class TaskRouter:

    """
    Celery tasks router.

    It allows us to decide which queue is where we want to execute the task
    based on project's settings but also in queue availability.

    1. the project is using conda
    2. new project with less than N successful builds
    3. last N successful builds have a high time average

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
            return settings.CELERY_DEFAULT_QUEUE

        # Do no route tasks for projects without the feature flag
        if not version.project.has_feature(Feature.CELERY_ROUTER):
            log.info('Project does not have the feature flag. No routing task. task=%s', task)
            return version.project.build_queue or settings.CELERY_DEFAULT_QUEUE

        # Do not override the queue defined in the project itself
        if version.project.build_queue:
            log.info(
                'Skipping routing task because project has a custom queue. queue=%s',
                version.project.build_queue,
            )
            return version.project.build_queue

        queryset = version.builds.filter(success=True).order_by('-date')
        last_builds = queryset[:self.N_LAST_BUILDS]

        # Version has used conda in previous builds
        for build in last_builds.iterator():
            if build.config.get('conda', None):
                log.info(
                    'Routing task because project uses conda. queue=%s',
                    self.BUILD_LARGE_QUEUE,
                )
                return self.BUILD_LARGE_QUEUE

        # We do not have enough builds for this version yet
        if queryset.count() < self.N_BUILDS:
            log.info(
                'Routing task because it does not have enough success builds yet. queue=%s',
                self.BUILD_LARGE_QUEUE,
            )
            return self.BUILD_LARGE_QUEUE

        # Build time average is high
        length_avg = queryset.filter(pk__in=last_builds).aggregate(Avg('length')).get('length__avg')
        if length_avg > self.TIME_AVERAGE:
            log.info(
                'Routing task because project has high time average. queue=%s',
                self.BUILD_LARGE_QUEUE,
            )
            return self.BUILD_LARGE_QUEUE

        log.info(
            'Routing task to default queue because no conditions were met. queue=%s',
            settings.CELERY_DEFAULT_QUEUE,
        )
        return settings.CELERY_DEFAULT_QUEUE

    def _get_version(self, task, args, kwargs):
        if task == 'readthedocs.projects.tasks.update_docs_task':
            build_pk = kwargs.get('build_pk')
            try:
                build = Build.objects.get(pk=build_pk)
                version = build.version
            except Build.DoesNotExist:
                log.info(
                    'Build does not exist. Routing task to default queue. build_pk=%s queue=%s',
                    build_pk,
                    settings.CELERY_DEFAULT_QUEUE,
                )
                return

        elif task == 'readthedocs.projects.tasks.sync_repository_task':
            version_pk = args[0]
            try:
                version = Version.objects.get(pk=version_pk)
            except Version.DoesNotExist:
                log.info(
                    'Version does not exist. Routing task to default queue. version_pk=%s queue=%s',
                    version_pk,
                    settings.CELERY_DEFAULT_QUEUE,
                )
                return
        return version
