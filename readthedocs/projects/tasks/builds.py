"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""
import signal
import socket
from collections import defaultdict

import structlog
from celery import Task
from django.conf import settings
from django.utils import timezone
from slumber.exceptions import HttpClientError

from readthedocs.api.v2.client import api as api_v2
from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_INSTALLING,
    BUILD_STATE_TRIGGERED,
    BUILD_STATE_UPLOADING,
    BUILD_STATUS_FAILURE,
    BUILD_STATUS_SUCCESS,
    EXTERNAL,
)
from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.builds.utils import memcache_lock
from readthedocs.config import ConfigError
from readthedocs.doc_builder.director import BuildDirector
from readthedocs.doc_builder.environments import (
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import (
    BuildAppError,
    BuildCancelled,
    BuildMaxConcurrencyError,
    BuildUserError,
    DuplicatedBuildError,
    MkDocsYAMLParseError,
    ProjectBuildsSkippedError,
    YAMLParseError,
)
from readthedocs.storage import build_media_storage
from readthedocs.telemetry.collectors import BuildDataCollector
from readthedocs.telemetry.tasks import save_build_data
from readthedocs.worker import app

from ..exceptions import (
    ProjectConfigurationError,
    RepositoryError,
    SyncRepositoryLocked,
)
from ..models import APIProject, Feature, WebHookEvent
from ..signals import before_vcs
from .mixins import SyncRepositoryMixin
from .search import fileify
from .utils import BuildRequest, clean_build, send_external_build_status

log = structlog.get_logger(__name__)


class TaskData:

    """
    Object to store all data related to a Celery task excecution.

    We use this object from inside the task to store data while we are runnig
    the task. This is to avoid using `self.` inside the task due to its
    limitations: it's instanciated once and that instance is re-used for all
    the tasks ran. This could produce sharing instance state between two
    different and unrelated tasks.

    Note that *all the data* that needs to be saved in the task to share among
    different task's method, should be stored in this object. Normally, under
    `self.data` inside the Celery task itself.

    See https://docs.celeryproject.org/en/master/userguide/tasks.html#instantiation
    """


class SyncRepositoryTask(SyncRepositoryMixin, Task):

    """
    Entry point to synchronize the VCS documentation.

    This task checks all the branches/tags from the external repository (by
    cloning) and update/sync the versions (by hitting the API) we have
    stored in the database to match these branches/tags.

    This task is executed on the builders and use the API to update the version
    in our database.
    """

    name = __name__ + '.sync_repository_task'
    max_retries = 5
    default_retry_delay = 7 * 60
    throws = (
        RepositoryError,
        SyncRepositoryLocked,
    )

    def before_start(self, task_id, args, kwargs):
        log.info('Running task.', name=self.name)

        # Create the object to store all the task-related data
        self.data = TaskData()

        self.data.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.data.environment_class = LocalBuildEnvironment

        # Comes from the signature of the task and it's the only required
        # argument
        version_id, = args

        # load all data from the API required for the build
        self.data.version = self.get_version(version_id)
        self.data.project = self.data.version.project

        # Also note there are builds that are triggered without a commit
        # because they just build the latest commit for that version
        self.data.build_commit = kwargs.get('build_commit')

        log.bind(
            project_slug=self.data.project.slug,
            version_slug=self.data.version.slug,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Do not log as error handled exceptions
        if isinstance(exc, RepositoryError):
            log.warning(
                'There was an error with the repository.',
            )
        elif isinstance(exc, SyncRepositoryLocked):
            log.warning(
                "Skipping syncing repository because there is another task running."
            )
        else:
            # Catch unhandled errors when syncing
            log.exception('An unhandled exception was raised during VCS syncing.')

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        clean_build(self.data.version)

    def execute(self):
        environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            environment={
                "GIT_TERMINAL_PROMPT": "0",
            },
            # Do not try to save commands on the db because they are just for
            # sync repository
            record=False,
        )

        with environment:
            before_vcs.send(
                sender=self.data.version,
                environment=environment,
            )

            vcs_repository = self.data.project.vcs_repo(
                version=self.data.version.slug,
                environment=environment,
                verbose_name=self.data.version.verbose_name,
                version_type=self.data.version.type,
            )
            if any(
                [
                    not vcs_repository.supports_lsremote,
                    not self.data.project.has_feature(Feature.VCS_REMOTE_LISTING),
                ]
            ):
                log.info("Syncing repository via full clone.")
                vcs_repository.update()
            else:
                log.info("Syncing repository via remote listing.")

            self.sync_versions(vcs_repository)


@app.task(
    base=SyncRepositoryTask,
    bind=True,
)
def sync_repository_task(self, version_id):
    lock_id = f"{self.name}-lock-{self.data.project.slug}"
    with memcache_lock(
        lock_id=lock_id, lock_expire=60, app_identifier=self.app.oid
    ) as lock_acquired:
        # Run `sync_repository_task` one at a time. If the task exceeds the 60
        # seconds, the lock is released and another task can be run in parallel
        # by a different worker.
        # See https://github.com/readthedocs/readthedocs.org/pull/9021/files#r828509016
        if not lock_acquired:
            raise SyncRepositoryLocked

        self.execute()


class UpdateDocsTask(SyncRepositoryMixin, Task):

    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported, was
    created or a webhook is received. Then it will sync the repository and
    build all the documentation formats and upload them to the storage.
    """

    name = __name__ + '.update_docs_task'
    autoretry_for = (
        BuildMaxConcurrencyError,
    )
    max_retries = settings.RTD_BUILDS_MAX_RETRIES
    default_retry_delay = settings.RTD_BUILDS_RETRY_DELAY
    retry_backoff = False

    # Expected exceptions that will be logged as info only and not retried.
    # These exceptions are not sent to Sentry either because we are using
    # ``SENTRY_CELERY_IGNORE_EXPECTED=True``.
    #
    # All exceptions generated by a user miss-configuration should be listed
    # here. Actually, every subclass of ``BuildUserError``.
    throws = (
        DuplicatedBuildError,
        ProjectBuildsSkippedError,
        ConfigError,
        YAMLParseError,
        BuildCancelled,
        BuildUserError,
        RepositoryError,
        MkDocsYAMLParseError,
        ProjectConfigurationError,
    )

    # Do not send notifications on failure builds for these exceptions.
    exceptions_without_notifications = (
        BuildCancelled,
        BuildMaxConcurrencyError,
        DuplicatedBuildError,
        ProjectBuildsSkippedError,
    )

    # Do not send external build status on failure builds for these exceptions.
    exceptions_without_external_build_status = (
        BuildMaxConcurrencyError,
        DuplicatedBuildError,
    )

    acks_late = True
    track_started = True

    # These values have to be dynamic based on project
    time_limit = None
    soft_time_limit = None

    Request = BuildRequest

    def _setup_sigterm(self):
        def sigterm_received(*args, **kwargs):
            log.warning('SIGTERM received. Waiting for build to stop gracefully after it finishes.')

        def sigint_received(*args, **kwargs):
            log.warning('SIGINT received. Canceling the build running.')
            raise BuildCancelled

        # Do not send the SIGTERM signal to children (pip is automatically killed when
        # receives SIGTERM and make the build to fail one command and stop build)
        signal.signal(signal.SIGTERM, sigterm_received)

        signal.signal(signal.SIGINT, sigint_received)

    def _check_concurrency_limit(self):
        try:
            response = api_v2.build.concurrent.get(project__slug=self.data.project.slug)
            concurrency_limit_reached = response.get('limit_reached', False)
            max_concurrent_builds = response.get(
                'max_concurrent',
                settings.RTD_MAX_CONCURRENT_BUILDS,
            )
        except Exception:
            log.exception(
                'Error while hitting/parsing API for concurrent limit checks from builder.',
                project_slug=self.data.project.slug,
                version_slug=self.data.version.slug,
            )
            concurrency_limit_reached = False
            max_concurrent_builds = settings.RTD_MAX_CONCURRENT_BUILDS

        if concurrency_limit_reached:
            # By calling ``retry`` Celery will raise an exception and call ``on_retry``.
            # NOTE: autoretry_for doesn't work with exceptions raised from before_start,
            # it only works if they are raised from the run/execute method.
            log.info("Concurrency limit reached, retrying task.")
            self.retry(
                exc=BuildMaxConcurrencyError(
                    BuildMaxConcurrencyError.message.format(
                        limit=max_concurrent_builds,
                    )
                )
            )

    def _check_duplicated_build(self):
        if self.data.build.get('status') == DuplicatedBuildError.status:
            log.warning('NOOP: build is marked as duplicated.')
            raise DuplicatedBuildError

    def _check_project_disabled(self):
        if self.data.project.skip:
            log.warning('Project build skipped.')
            raise ProjectBuildsSkippedError

    def before_start(self, task_id, args, kwargs):
        # Create the object to store all the task-related data
        self.data = TaskData()

        # Comes from the signature of the task and they are the only
        # required arguments.
        self.data.version_pk, self.data.build_pk = args

        log.bind(build_id=self.data.build_pk)
        log.info("Running task.", name=self.name)

        self.data.start_time = timezone.now()
        self.data.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.data.environment_class = LocalBuildEnvironment

        self.data.build = self.get_build(self.data.build_pk)
        self.data.version = self.get_version(self.data.version_pk)
        self.data.project = self.data.version.project

        # Save the builder instance's name into the build object
        self.data.build['builder'] = socket.gethostname()

        # Reset any previous build error reported to the user
        self.data.build['error'] = ''

        self.data.build_data = None

        # Also note there are builds that are triggered without a commit
        # because they just build the latest commit for that version
        self.data.build_commit = kwargs.get('build_commit')

        log.bind(
            # NOTE: ``self.data.build`` is just a regular dict, not an APIBuild :'(
            builder=self.data.build['builder'],
            commit=self.data.build_commit,
            project_slug=self.data.project.slug,
            version_slug=self.data.version.slug,
        )

        # Clean the build paths completely to avoid conflicts with previous run
        # (e.g. cleanup task failed for some reason)
        clean_build(self.data.version)

        # NOTE: this is never called. I didn't find anything in the logs, so we
        # can probably remove it
        self._setup_sigterm()

        self._check_project_disabled()
        self._check_duplicated_build()
        self._check_concurrency_limit()
        self._reset_build()

    def _reset_build(self):
        # Reset build only if it has some commands already.
        if self.data.build.get("commands"):
            log.info("Reseting build.")
            api_v2.build(self.data.build["id"]).reset.post()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.info("Task failed.")
        if not hasattr(self.data, 'build'):
            # NOTE: use `self.data.build_id` (passed to the task) instead
            # `self.data.build` (retrieved from the API) because it's not present,
            # probably due the API failed when retrieving it.
            #
            # So, we create the `self.data.build` with the minimum required data.
            self.data.build = {
                'id': self.data.build_pk,
            }

        # TODO: handle this `ConfigError` as a `BuildUserError` in the
        # following block
        if isinstance(exc, ConfigError):
            self.data.build['error'] = str(
                YAMLParseError(
                    YAMLParseError.GENERIC_WITH_PARSE_EXCEPTION.format(
                        exception=str(exc),
                    ),
                ),
            )
        # Known errors in our application code (e.g. we couldn't connect to
        # Docker API). Report a generic message to the user.
        elif isinstance(exc, BuildAppError):
            self.data.build['error'] = BuildAppError.GENERIC_WITH_BUILD_ID.format(
                build_id=self.data.build['id'],
            )
        # Known errors in the user's project (e.g. invalid config file, invalid
        # repository, command failed, etc). Report the error back to the user
        # using the `message` attribute from the exception itself. Otherwise,
        # use a generic message.
        elif isinstance(exc, BuildUserError):
            if hasattr(exc, 'message') and exc.message is not None:
                self.data.build['error'] = exc.message
            else:
                self.data.build['error'] = BuildUserError.GENERIC
        else:
            # We don't know what happened in the build. Log the exception and
            # report a generic message to the user.
            log.exception('Build failed with unhandled exception.')
            self.data.build['error'] = BuildAppError.GENERIC_WITH_BUILD_ID.format(
                build_id=self.data.build['id'],
            )

        # Send notifications for unhandled errors
        if not isinstance(exc, self.exceptions_without_notifications):
            self.send_notifications(
                self.data.version.pk,
                self.data.build['id'],
                event=WebHookEvent.BUILD_FAILED,
            )

        # NOTE: why we wouldn't have `self.data.build_commit` here?
        # This attribute is set when we get it after clonning the repository
        #
        # Oh, I think this is to differentiate a task triggered with
        # `Build.commit` than a one triggered just with the `Version` to build
        # the _latest_ commit of it
        if self.data.build_commit and not isinstance(
            exc, self.exceptions_without_external_build_status
        ):
            send_external_build_status(
                version_type=self.data.version.type,
                build_pk=self.data.build['id'],
                commit=self.data.build_commit,
                status=BUILD_STATUS_FAILURE,
            )

        # Update build object
        self.data.build['success'] = False

    def on_success(self, retval, task_id, args, kwargs):
        html = self.data.outcomes['html']
        search = self.data.outcomes['search']
        localmedia = self.data.outcomes['localmedia']
        pdf = self.data.outcomes['pdf']
        epub = self.data.outcomes['epub']

        # Store build artifacts to storage (local or cloud storage)
        self.store_build_artifacts(
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
                api_v2.version(self.data.version.pk).patch(
                    {
                        "built": True,
                        "documentation_type": self.data.version.documentation_type,
                        "has_pdf": pdf,
                        "has_epub": epub,
                        "has_htmlzip": localmedia,
                    }
                )
            except HttpClientError:
                # NOTE: I think we should fail the build if we cannot update
                # the version at this point. Otherwise, we will have inconsistent data
                log.exception(
                    'Updating version failed, skipping file sync.',
                )

        # Index search data
        fileify.delay(
            version_pk=self.data.version.pk,
            commit=self.data.build['commit'],
            build=self.data.build['id'],
            search_ranking=self.data.config.search.ranking,
            search_ignore=self.data.config.search.ignore,
        )

        if not self.data.project.has_valid_clone:
            self.set_valid_clone()

        self.send_notifications(
            self.data.version.pk,
            self.data.build['id'],
            event=WebHookEvent.BUILD_PASSED,
        )

        if self.data.build_commit:
            send_external_build_status(
                version_type=self.data.version.type,
                build_pk=self.data.build['id'],
                commit=self.data.build_commit,
                status=BUILD_STATUS_SUCCESS,
            )

        # Update build object
        self.data.build['success'] = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Celery helper called when the task is retried.

        This happens when any of the exceptions defined in ``autoretry_for``
        argument is raised or when ``self.retry`` is called from inside the
        task.

        See https://docs.celeryproject.org/en/master/userguide/tasks.html#retrying
        """
        log.info('Retrying this task.')

        if isinstance(exc, BuildMaxConcurrencyError):
            log.warning(
                'Delaying tasks due to concurrency limit.',
                project_slug=self.data.project.slug,
                version_slug=self.data.version.slug,
            )
            self.data.build['error'] = exc.message
            self.update_build(state=BUILD_STATE_TRIGGERED)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # Update build object
        self.data.build['length'] = (timezone.now() - self.data.start_time).seconds

        self.update_build(BUILD_STATE_FINISHED)
        self.save_build_data()

        build_complete.send(sender=Build, build=self.data.build)

        clean_build(self.data.version)

        log.info(
            'Build finished.',
            length=self.data.build['length'],
            success=self.data.build['success']
        )

    def update_build(self, state):
        self.data.build['state'] = state

        # Attempt to stop unicode errors on build reporting
        # for key, val in list(self.data.build.items()):
        #     if isinstance(val, bytes):
        #         self.data.build[key] = val.decode('utf-8', 'ignore')

        try:
            api_v2.build(self.data.build['id']).patch(self.data.build)
        except Exception:
            # NOTE: I think we should fail the build if we cannot update it
            # at this point otherwise, the data will be inconsistent and we
            # may be serving "new docs" but saying the "build have failed"
            log.exception('Unable to update build')

    def execute(self):
        self.data.build_director = BuildDirector(
            data=self.data,
        )

        # Clonning
        self.update_build(state=BUILD_STATE_CLONING)

        # TODO: remove the ``create_vcs_environment`` hack. Ideally, this should be
        # handled inside the ``BuildDirector`` but we can't use ``with
        # self.vcs_environment`` twice because it kills the container on
        # ``__exit__``
        self.data.build_director.create_vcs_environment()
        with self.data.build_director.vcs_environment:
            self.data.build_director.setup_vcs()

            # Sync tags/branches from VCS repository into Read the Docs'
            # `Version` objects in the database. This method runs commands
            # (e.g. "hg tags") inside the VCS environment, so it requires to be
            # inside the `with` statement
            self.sync_versions(self.data.build_director.vcs_repository)

        # TODO: remove the ``create_build_environment`` hack. Ideally, this should be
        # handled inside the ``BuildDirector`` but we can't use ``with
        # self.build_environment`` twice because it kills the container on
        # ``__exit__``
        self.data.build_director.create_build_environment()
        with self.data.build_director.build_environment:
            try:
                # NOTE: check if the build uses `build.commands` and only run those
                if self.data.config.build.commands:
                    self.update_build(state=BUILD_STATE_BUILDING)
                    self.data.build_director.run_build_commands()

                    self.data.outcomes = defaultdict(lambda: False)
                    self.data.outcomes["html"] = True
                else:
                    # Installing
                    self.update_build(state=BUILD_STATE_INSTALLING)
                    self.data.build_director.setup_environment()

                    # Building
                    self.update_build(state=BUILD_STATE_BUILDING)
                    self.data.build_director.build()
            finally:
                self.data.build_data = self.collect_build_data()

    def collect_build_data(self):
        """
        Collect data from the current build.

        The data is collected from inside the container,
        so this must be called before killing the container.
        """
        try:
            return BuildDataCollector(
                self.data.build_director.build_environment
            ).collect()
        except Exception:
            log.exception("Error while collecting build data")

    def save_build_data(self):
        """
        Save the data collected from the build after it has ended.

        This must be called after the build has finished updating its state,
        otherwise some attributes like ``length`` won't be available.
        """
        try:
            if self.data.build_data:
                save_build_data.delay(
                    build_id=self.data.build_pk,
                    data=self.data.build_data,
                )
        except Exception:
            log.exception("Error while saving build data")

    @staticmethod
    def get_project(project_pk):
        """Get project from API."""
        project_data = api_v2.project(project_pk).get()
        return APIProject(**project_data)

    @staticmethod
    def get_build(build_pk):
        """
        Retrieve build object from API.

        :param build_pk: Build primary key
        """
        build = {}
        if build_pk:
            build = api_v2.build(build_pk).get()
        private_keys = [
            'project',
            'version',
            'resource_uri',
            'absolute_uri',
        ]
        # TODO: try to use the same technique than for ``APIProject``.
        return {
            key: val
            for key, val in build.items() if key not in private_keys
        }

    # NOTE: this can be just updated on `self.data.build['']` and sent once the
    # build has finished to reduce API calls.
    def set_valid_clone(self):
        """Mark on the project that it has been cloned properly."""
        api_v2.project(self.data.project.pk).patch(
            {'has_valid_clone': True}
        )
        self.data.project.has_valid_clone = True
        self.data.version.project.has_valid_clone = True

    def store_build_artifacts(
            self,
            html=False,
            localmedia=False,
            search=False,
            pdf=False,
            epub=False,
    ):
        """
        Save build artifacts to "storage" using Django's storage API.

        The storage could be local filesystem storage OR cloud blob storage
        such as S3, Azure storage or Google Cloud Storage.

        Remove build artifacts of types not included in this build (PDF, ePub, zip only).

        :param html: whether to save HTML output
        :param localmedia: whether to save localmedia (htmlzip) output
        :param search: whether to save search artifacts
        :param pdf: whether to save PDF output
        :param epub: whether to save ePub output
        """
        log.info('Writing build artifacts to media storage')
        # NOTE: I don't remember why we removed this state from the Build
        # object. I'm re-adding it because I think it's useful, but we can
        # remove it if we want
        self.update_build(state=BUILD_STATE_UPLOADING)

        types_to_copy = []
        types_to_delete = []

        # HTML media
        if html:
            types_to_copy.append(('html', self.data.config.doctype))

        # Search media (JSON)
        if search:
            types_to_copy.append(('json', 'sphinx_search'))

        if localmedia:
            types_to_copy.append(('htmlzip', 'sphinx_localmedia'))
        else:
            types_to_delete.append('htmlzip')

        if pdf:
            types_to_copy.append(('pdf', 'sphinx_pdf'))
        else:
            types_to_delete.append('pdf')

        if epub:
            types_to_copy.append(('epub', 'sphinx_epub'))
        else:
            types_to_delete.append('epub')

        for media_type, build_type in types_to_copy:
            from_path = self.data.version.project.artifact_path(
                version=self.data.version.slug,
                type_=build_type,
            )
            to_path = self.data.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.data.version.slug,
                include_file=False,
                version_type=self.data.version.type,
            )
            try:
                build_media_storage.sync_directory(from_path, to_path)
            except Exception:
                # Ideally this should just be an IOError
                # but some storage backends unfortunately throw other errors
                log.exception(
                    'Error copying to storage (not failing build)',
                    media_type=media_type,
                    from_path=from_path,
                    to_path=to_path,
                )

        for media_type in types_to_delete:
            media_path = self.data.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.data.version.slug,
                include_file=False,
                version_type=self.data.version.type,
            )
            try:
                build_media_storage.delete_directory(media_path)
            except Exception:
                # Ideally this should just be an IOError
                # but some storage backends unfortunately throw other errors
                log.exception(
                    'Error deleting from storage (not failing build)',
                    media_type=media_type,
                    media_path=media_path,
                )

    def send_notifications(self, version_pk, build_pk, event):
        """Send notifications to all subscribers of `event`."""
        # Try to infer the version type if we can
        # before creating a task.
        if not self.data.version or self.data.version.type != EXTERNAL:
            build_tasks.send_build_notifications.delay(
                version_pk=version_pk,
                build_pk=build_pk,
                event=event,
            )


@app.task(
    base=UpdateDocsTask,
    bind=True,
    ignore_result=True,
)
def update_docs_task(self, version_id, build_id, build_commit=None):
    self.execute()
