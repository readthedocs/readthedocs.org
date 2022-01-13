import signal
import socket

import structlog

from celery import Task
from celery.worker.request import Request
from celery.exceptions import SoftTimeLimitExceeded

from django.conf import settings
from readthedocs.api.v2.client import api as api_v2
from readthedocs.builds.constants import BUILD_STATE_FINISHED, BUILD_STATUS_SUCCESS
from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.config.config import ConfigError
from readthedocs.doc_builder.environments import (
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import (
    BuildEnvironmentError,
    BuildEnvironmentException,
    BuildEnvironmentWarning,
    BuildMaxConcurrencyError,
    DuplicatedBuildError,
    VersionLockedError,
    ProjectBuildsSkippedError,
    YAMLParseError,
)
from readthedocs.projects.models import WebHookEvent

from .search import fileify
from .utils import clean_build


log = structlog.get_logger(__name__)


class BuildRequest(Request):

    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)
        log.bind(
            task_name=self.task.name,
            project_slug=self.task.args.project_slug,
            build_id=self.task.args.build_id,
            timeout=timeout,
            soft=soft,
        )
        if soft:
            log.warning('Build is taking too much time. Risk to be killed soon.')
        else:
            log.warning('A timeout was enforced for task.')


# NOTE: consider calling it a mixin
class BuildTaskBase:

    autoretry_for = (
        BuildMaxConcurrencyError,
    )
    max_retries = 5  # 5 per normal builds, 25 per concurrency limited
    default_retry_delay = 7 * 60

    # Expected exceptions that will be logged as info only and not retried
    throws = (
        DuplicatedBuildError,
        VersionLockedError,
        ProjectBuildsSkippedError,
        ConfigError,
        YAMLParseError,
    )

    acks_late = True
    track_started = True

    # These values have to be dynamic based on project
    time_limit = None
    soft_time_limit = None

    Request = BuildRequest

    # 1. raise Reject(requeue=False) on duplicated builds
    # 2. use a global `task_cls` (https://docs.celeryproject.org/en/latest/userguide/tasks.html#app-wide-usage) to logs actions
    # 3. use CELERY_IMPORTS to register the tasks (https://docs.celeryproject.org/en/latest/userguide/configuration.html#std-setting-imports)
    # 4. use CELERY_TASK_IGNORE_RESULT=True since we are not using the result at all


    def _setup_sigterm(self):
        def sigterm_received(*args, **kwargs):
            log.warning('SIGTERM received. Waiting for build to stop gracefully after it finishes.')

        # Do not send the SIGTERM signal to children (pip is automatically killed when
        # receives SIGTERM and make the build to fail one command and stop build)
        signal.signal(signal.SIGTERM, sigterm_received)

    def _check_concurrency_limit(self):
        try:
            response = api_v2.build.concurrent.get(project__slug=self.project.slug)
            concurrency_limit_reached = response.get('limit_reached', False)
            max_concurrent_builds = response.get(
                'max_concurrent',
                settings.RTD_MAX_CONCURRENT_BUILDS,
            )
        except Exception:
            log.exception(
                'Error while hitting/parsing API for concurrent limit checks from builder.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
            )
            concurrency_limit_reached = False
            max_concurrent_builds = settings.RTD_MAX_CONCURRENT_BUILDS

        if concurrency_limit_reached:
            log.warning(
                'Delaying tasks due to concurrency limit.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
            )

            # This is done automatically on the environment context, but
            # we are executing this code before creating one
            api_v2.build(self.build['id']).patch({
                'error': BuildMaxConcurrencyError.message.format(
                    limit=max_concurrent_builds,
                ),
                'builder': socket.gethostname(),
            })
            self.task.retry(
                exc=BuildMaxConcurrencyError,
                throw=False,
                # We want to retry this build more times
                max_retries=25,
            )
            return False

    def _check_duplicated_build(self):
        if self.build.get('status') == DuplicatedBuildError.status:
            log.warning('NOOP: build is marked as duplicated.')
            raise DuplicatedBuildError

    def _check_project_disabled(self):
        if self.project.skip:
            log.warning('Project build skipped.')
            raise ProjectBuildsSkippedError

    def before_start(self, task_id, args, kwargs):
        log.info('Running task.', name=self.name)

        # NOTE: save all the attributes to do a clean up when finish
        self._attributes = list(self.__dict__.keys()) + ['_attributes']

        self.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.environment_class = LocalBuildEnvironment

        version_pk = kwargs.get('version_pk')
        build_pk = kwargs.get('build_pk')

        self.commit = kwargs.get('commit')
        self.record = kwargs.get('record')
        self.force = kwargs.get('force')

        self.build = self.get_build(build_pk)
        self.version = self.get_version(version_pk)
        self.project = self.version.project

        log.bind(
            # NOTE: ``self.build`` is just a regular dict, not an APIBuild :'(
            build_id=self.build['id'],
            commit=self.commit,
            project_slug=self.project.slug,
            version_slug=self.version.slug,
            force=self.force,
            record=self.record,
        )

        # NOTE: this is never called. I didn't find anything in the logs, so we can probably remove it
        self._setup_sigterm()

        self._check_project_disabled()
        self._check_duplicated_build()
        self._check_concurrency_limit()
        self._reset_build()

    def _reset_build(self):
        # Reset build only if it has some commands already.
        if self.build.get('commands'):
            api_v2.build(self.build['id']).reset.post()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Take a proper action based on the ``exc``. For example, if
        # ``vcs_support_utils.LockTimeout`` retry the task. Note that some
        # exceptions may require access to the ``environment`` variable to
        # update the context (hiting the API to set the build status)

        # NOTE: find where this exception is defined
        # if exc is HardTimeLimitExceeded:
        #     log.warning('Build killed because timeout.')

        if isinstance(exc, ConfigError):
            self.build['error'] = str(
                YAMLParseError(
                    YAMLParseError.GENERIC_WITH_PARSE_EXCEPTION.format(
                        exception=str(exc),
                    ),
                ),
            )
        elif isinstance(exc, ProjectBuildsSkippedError):
            # TODO: test if `on_failure` is called when it's an expected
            # exception (e.g. defined in `throws=`). I would expect that this
            # method is not called.
            log.info('ProjectBuildsSkippedError exception')
        elif isinstance(exc, BuildEnvironmentError):
            # TODO: if the exceptions are known we can just copy the message here
            self.build['error'] = exc.msg
        else:
            log.exception('Build failed with unhandled exception.')
            self.build['error'] = str(
                BuildEnvironmentError(
                    BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                        build_id=self.build['id'],
                    ),
                ),
            )

        # NOTE: all the locking code may be removed, so this is not important anymore
        # TODO: do not send notifications on ``VersionLockedError``
        # (vcs_support_utils.LockTimeout) since it's not a problem for the user

        # Send notifications for unhandled errors
        self.send_notifications(
            self.version.pk,
            self.build['id'],
            event=WebHookEvent.BUILD_FAILED,
        )

        # NOTE: why we wouldn't have `self.commit` here?
        if self.commit:
            send_external_build_status(
                version_type=self.version.type,
                build_pk=self.build['id'],
                commit=self.commit,
                status=BUILD_STATUS_FAILURE,
            )


        # Update build object
        self.build['success'] = False
        if hasattr(exc, 'status_code'):
            self.build['exit_code'] = exc.status_code

    def on_success(self, retval, task_id, args, kwargs):
        build_id = self.build.get('id')

        html = self.outcomes['html']
        search = self.outcomes['search']
        localmedia = self.outcomes['localmedia']
        pdf = self.outcomes['pdf']
        epub = self.outcomes['epub']

        # Store build artifacts to storage (local or cloud storage)
        self.store_build_artifacts(
            self.build_env,
            html=html,
            search=search,
            localmedia=localmedia,
            pdf=pdf,
            epub=epub,
        )

        # NOTE: we are updating the db version instance *only* when
        # HTML are built successfully.
        if html:
            try:
                version = api_v2.version(self.version.pk)
                version.patch({
                    'built': True,
                    'documentation_type': self.get_final_doctype(),
                    'has_pdf': pdf,
                    'has_epub': epub,
                    'has_htmlzip': localmedia,
                })
            except HttpClientError:
                log.exception(
                    'Updating version failed, skipping file sync.',
                )

        # Index search data
        fileify.delay(
            version_pk=self.version.pk,
            commit=self.build['commit'],
            build=self.build['id'],
            search_ranking=self.config.search.ranking,
            search_ignore=self.config.search.ignore,
        )


        # send build status to github
        # send webhook notification
        # emit django signal for build success
        if not self.project.has_valid_clone:
            self.set_valid_clone()

        self.send_notifications(
            self.version.pk,
            self.build['id'],
            event=WebHookEvent.BUILD_PASSED,
        )

        # NOTE: why we wouldn't have `self.commit` here?
        if self.commit:
            send_external_build_status(
                version_type=self.version.type,
                build_pk=self.build['id'],
                commit=self.commit,
                status=BUILD_STATUS_SUCCESS,
            )

        # Update build object
        self.build['success'] = True
        # self.build['exit_code'] = max([
        #     cmd.exit_code for cmd in self.builds['commands']
        # ])


    def on_retry(self, exc, task_id, args, kwargs, einfo):
        pass

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # Update build object
        self.build['setup'] = self.build['setup_error'] = ''
        self.build['output'] = self.build['error'] = ''
        self.build['builder'] = socket.gethostname()

        # from celery.contrib import rdb; rdb.set_trace()


        # TODO: get the start time from the task itself
        # self.build['length'] = self.request.start_time

        self.update_build(BUILD_STATE_FINISHED)

        build_complete.send(sender=Build, build=self.build)

        clean_build(self.version.pk)

        # HACK: cleanup all the attributes set by the task under `self`
        for attribute in list(self.__dict__.keys()):
            if attribute not in self._attributes:
                del self.__dict__[attribute]

    def update_build(self, state):
        self.build['state'] = state

        if self.record:
            # Attempt to stop unicode errors on build reporting
            # for key, val in list(self.build.items()):
            #     if isinstance(val, bytes):
            #         self.build[key] = val.decode('utf-8', 'ignore')

            try:
                api_v2.build(self.build['id']).patch(self.build)
            except Exception:
                log.exception('Unable to update build')
