import json
import logging
from datetime import datetime, timedelta
from io import BytesIO

from celery import Task
from django.conf import settings

from readthedocs.api.v2.serializers import BuildSerializer
from readthedocs.api.v2.utils import (
    delete_versions_from_db,
    get_deleted_active_versions,
    run_automation_rules,
    sync_versions_to_db,
)
from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    BUILD_STATUS_FAILURE,
    BUILD_STATUS_PENDING,
    BUILD_STATUS_SUCCESS,
    MAX_BUILD_COMMAND_SIZE,
    TAG,
)
from readthedocs.builds.models import Build, Version
from readthedocs.builds.utils import memcache_lock
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import send_build_status
from readthedocs.storage import build_commands_storage
from readthedocs.worker import app

log = logging.getLogger(__name__)


class TaskRouter:

    """
    Celery tasks router.

    It allows us to decide which queue is where we want to execute the task
    based on project's settings.

    1. the project is using conda
    2. new project with less than N successful builds
    3. version to be built is external

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

        # Use last queue used by the default version for external versions
        # We always want the same queue as the previous default version,
        # so that users will have the same outcome for PR's as normal builds.
        if version.type == EXTERNAL:
            last_build_for_default_version = (
                project.builds
                .filter(version__slug=project.get_default_version(), builder__isnull=False)
                .order_by('-date')
                .first()
            )
            if last_build_for_default_version:
                if 'default' in last_build_for_default_version.builder:
                    routing_queue = self.BUILD_DEFAULT_QUEUE
                else:
                    routing_queue = self.BUILD_LARGE_QUEUE
                log.info(
                    'Routing task because is a external version. project=%s queue=%s',
                    project.slug, routing_queue,
                )
                return routing_queue

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

    for build in queryset:
        data = BuildSerializer(build).data['commands']
        if data:
            for cmd in data:
                if len(cmd['output']) > MAX_BUILD_COMMAND_SIZE:
                    cmd['output'] = cmd['output'][-MAX_BUILD_COMMAND_SIZE:]
                    cmd['output'] = "... (truncated) ...\n\nCommand output too long. Truncated to last 1MB.\n\n" + cmd['output']  # noqa
                    log.warning('Truncating build command for build. build=%s', build.pk)
            output = BytesIO()
            output.write(json.dumps(data).encode('utf8'))
            output.seek(0)
            filename = '{date}/{id}.json'.format(date=str(build.date.date()), id=build.id)
            try:
                build_commands_storage.save(name=filename, content=output)
                build.cold_storage = True
                build.save()
                if delete:
                    build.commands.all().delete()
            except IOError:
                log.exception('Cold Storage save failure')


@app.task(queue='web')
def delete_inactive_external_versions(limit=200, days=30 * 3):
    """
    Delete external versions that have been marked as inactive after ``days``.

    The commit status is updated to link to the build page, as the docs are removed.
    """
    days_ago = datetime.now() - timedelta(days=days)
    queryset = Version.external.filter(
        active=False,
        modified__lte=days_ago,
    )[:limit]
    for version in queryset:
        try:
            last_build = version.last_build
            if last_build:
                status = BUILD_STATUS_PENDING
                if last_build.finished:
                    status = BUILD_STATUS_SUCCESS if last_build.success else BUILD_STATUS_FAILURE
                send_build_status(
                    build_pk=last_build.pk,
                    commit=last_build.commit,
                    status=status,
                    link_to_build=True,
                )
        except Exception:
            log.exception(
                "Failed to send status: project=%s version=%s",
                version.project.slug, version.slug,
            )
        else:
            log.info(
                "Removing external version. project=%s version=%s",
                version.project.slug, version.slug,
            )
            version.delete()


@app.task(
    max_retries=1,
    default_retry_delay=60,
    queue='web'
)
def sync_versions_task(project_pk, tags_data, branches_data, **kwargs):
    """
    Sync the version data in the repo (from build server) into our database.

    Creates new Version objects for tags/branches that aren't tracked in the database,
    and deletes Version objects for tags/branches that don't exists in the repository.

    :param tags_data: List of dictionaries with ``verbose_name`` and ``identifier``.
    :param branches_data: Same as ``tags_data`` but for branches.
    :returns: the identifiers for the versions that have been deleted.
    """
    project = Project.objects.get(pk=project_pk)

    # If the currently highest non-prerelease version is active, then make
    # the new latest version active as well.
    current_stable = project.get_original_stable_version()
    if current_stable is not None:
        activate_new_stable = current_stable.active
    else:
        activate_new_stable = False

    try:
        # Update All Versions
        added_versions = set()
        result = sync_versions_to_db(
            project=project,
            versions=tags_data,
            type=TAG,
        )
        added_versions.update(result)

        result = sync_versions_to_db(
            project=project,
            versions=branches_data,
            type=BRANCH,
        )
        added_versions.update(result)

        deleted_versions = delete_versions_from_db(
            project=project,
            tags_data=tags_data,
            branches_data=branches_data,
        )
        deleted_active_versions = get_deleted_active_versions(
            project=project,
            tags_data=tags_data,
            branches_data=branches_data,
        )
    except Exception:
        log.exception('Sync Versions Error')
        return [], []

    try:
        # The order of added_versions isn't deterministic.
        # We don't track the commit time or any other metadata.
        # We usually have one version added per webhook.
        run_automation_rules(project, added_versions, deleted_active_versions)
    except Exception:
        # Don't interrupt the request if something goes wrong
        # in the automation rules.
        log.exception(
            'Failed to execute automation rules for [%s]: %s',
            project.slug, added_versions
        )

    # TODO: move this to an automation rule
    promoted_version = project.update_stable_version()
    new_stable = project.get_stable_version()
    if promoted_version and new_stable and new_stable.active:
        log.info(
            'Triggering new stable build: %(project)s:%(version)s',
            {
                'project': project.slug,
                'version': new_stable.identifier,
            }
        )
        trigger_build(project=project, version=new_stable)

        # Marking the tag that is considered the new stable version as
        # active and building it if it was just added.
        if (
            activate_new_stable and
            promoted_version.slug in added_versions
        ):
            promoted_version.active = True
            promoted_version.save()
            trigger_build(project=project, version=promoted_version)

    return list(added_versions), list(deleted_versions)
