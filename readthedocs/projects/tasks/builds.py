"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""

import datetime
import os
import shutil
import signal
import socket
import subprocess
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import structlog
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.utils import timezone
from slumber import API
from slumber.exceptions import HttpClientError

from readthedocs.api.v2.client import setup_api
from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import ARTIFACT_TYPES
from readthedocs.builds.constants import ARTIFACT_TYPES_WITHOUT_MULTIPLE_FILES_SUPPORT
from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE_BUILDING
from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.builds.constants import BUILD_STATE_CLONING
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_INSTALLING
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import BUILD_STATE_UPLOADING
from readthedocs.builds.constants import BUILD_STATUS_FAILURE
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import UNDELETABLE_ARTIFACT_TYPES
from readthedocs.builds.models import APIVersion
from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.builds.utils import memcache_lock
from readthedocs.config.config import BuildConfigV2
from readthedocs.config.exceptions import ConfigError
from readthedocs.core.utils.filesystem import assert_path_is_inside_docroot
from readthedocs.doc_builder.director import BuildDirector
from readthedocs.doc_builder.environments import DockerBuildEnvironment
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.doc_builder.exceptions import BuildCancelled
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.doc_builder.exceptions import MkDocsYAMLParseError
from readthedocs.projects.models import Feature
from readthedocs.projects.tasks.storage import StorageType
from readthedocs.projects.tasks.storage import get_storage
from readthedocs.telemetry.collectors import BuildDataCollector
from readthedocs.telemetry.tasks import save_build_data
from readthedocs.worker import app

from ..exceptions import ProjectConfigurationError
from ..exceptions import RepositoryError
from ..exceptions import SyncRepositoryLocked
from ..models import APIProject
from ..models import WebHookEvent
from ..signals import before_vcs
from .mixins import SyncRepositoryMixin
from .search import index_build
from .utils import BuildRequest
from .utils import clean_build
from .utils import send_external_build_status
from .utils import set_builder_scale_in_protection


log = structlog.get_logger(__name__)


# With slots=True we can't add additional attributes
# than the ones declared in the dataclass.
@dataclass(slots=True)
class TaskData:
    """
    Object to store all data related to a Celery task execution.

    We use this object from inside the task to store data while we are running
    the task. This is to avoid using `self.` inside the task due to its
    limitations: it's instantiated once and that instance is re-used for all
    the tasks ran. This could produce sharing instance state between two
    different and unrelated tasks.

    Note that *all the data* that needs to be saved in the task to share among
    different task's method, should be stored in this object. Normally, under
    `self.data` inside the Celery task itself.

    See https://docs.celeryproject.org/en/master/userguide/tasks.html#instantiation

    .. note::

       Dataclasses require type annotations, this doesn't mean we are using
       type hints or enforcing them in our codebase.
    """

    # Arguments from the task.
    version_pk: int = None
    build_pk: int = None
    build_commit: str = None

    # Slumber client to interact with the API v2.
    api_client: API = None

    start_time: timezone.datetime = None
    environment_class: type[DockerBuildEnvironment] | type[LocalBuildEnvironment] = None
    build_director: BuildDirector = None
    config: BuildConfigV2 = None
    project: APIProject = None
    version: APIVersion = None
    # Default branch for the repository.
    # Only set when building the latest version, and the project
    # doesn't have an explicit default branch.
    default_branch: str | None = None

    # Dictionary returned from the API.
    build: dict = field(default_factory=dict)
    # Build data for analytics (telemetry).
    build_data: dict = field(default_factory=dict)


class SyncRepositoryTask(SyncRepositoryMixin, Task):
    """
    Entry point to synchronize the VCS documentation.

    This task checks all the branches/tags from the external repository (by
    cloning) and update/sync the versions (by hitting the API) we have
    stored in the database to match these branches/tags.

    This task is executed on the builders and use the API to update the version
    in our database.
    """

    name = __name__ + ".sync_repository_task"
    max_retries = 5
    default_retry_delay = 7 * 60
    throws = (
        RepositoryError,
        SyncRepositoryLocked,
    )

    def before_start(self, task_id, args, kwargs):
        log.info("Running task.", name=self.name)

        # Create the object to store all the task-related data
        self.data = TaskData()

        self.data.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.data.environment_class = LocalBuildEnvironment

        # Comes from the signature of the task and it's the only required
        # argument
        self.data.version_pk = args[0]

        self.data.api_client = setup_api(kwargs["build_api_key"])

        # load all data from the API required for the build
        self.data.version = self.get_version(self.data.version_pk)
        self.data.project = self.data.version.project

        # Also note there are builds that are triggered without a commit
        # because they just build the latest commit for that version
        self.data.build_commit = kwargs.get("build_commit")

        structlog.contextvars.bind_contextvars(
            project_slug=self.data.project.slug,
            version_slug=self.data.version.slug,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Do not log as error handled exceptions
        if isinstance(exc, RepositoryError):
            log.warning(
                "There was an error with the repository.",
            )
        elif isinstance(exc, SyncRepositoryLocked):
            log.warning("Skipping syncing repository because there is another task running.")
        else:
            # Catch unhandled errors when syncing
            # Note we are using `log.error(exc_info=...)` instead of `log.exception`
            # because this is not executed inside a try/except block.
            log.error("An unhandled exception was raised during VCS syncing.", exc_info=exc)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Celery handler to be executed after a task runs.

        .. note::

           This handler is called even if the task has failed,
           so some attributes from the `self.data` object may not be defined.
        """
        if self.data.version:
            clean_build(self.data.version)

    def execute(self):
        environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            environment={
                "GIT_TERMINAL_PROMPT": "0",
                "READTHEDOCS_GIT_CLONE_TOKEN": self.data.project.clone_token,
            },
            # Pass the api_client so that all environments have it.
            # This is needed for ``readthedocs-corporate``.
            api_client=self.data.api_client,
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
                version=self.data.version,
                environment=environment,
            )
            log.info("Syncing repository via remote listing.")
            self.sync_versions(vcs_repository)


@app.task(
    base=SyncRepositoryTask,
    bind=True,
)
def sync_repository_task(self, version_id, *, build_api_key, **kwargs):
    # In case we pass more arguments than expected, log them and ignore them,
    # so we don't break builds while we deploy a change that requires an extra argument.
    if kwargs:
        log.warning("Extra arguments passed to sync_repository_task", arguments=kwargs)
    lock_id = f"{self.name}-lock-{self.data.project.slug}"
    with memcache_lock(
        lock_id=lock_id, lock_expire=60, app_identifier=self.app.oid
    ) as lock_acquired:
        # Run `sync_repository_task` one at a time. If the task exceeds the 60
        # seconds, the lock is released and another task can be run in parallel
        # by a different worker.
        # See https://github.com/readthedocs/readthedocs.org/pull/9021/files#r828509016
        if not lock_acquired:
            raise SyncRepositoryLocked(SyncRepositoryLocked.REPOSITORY_LOCKED)

        self.execute()


class UpdateDocsTask(SyncRepositoryMixin, Task):
    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported, was
    created or a webhook is received. Then it will sync the repository and
    build all the documentation formats and upload them to the storage.
    """

    name = __name__ + ".update_docs_task"
    autoretry_for = (BuildMaxConcurrencyError,)
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
        ConfigError,
        BuildCancelled,
        BuildUserError,
        RepositoryError,
        MkDocsYAMLParseError,
        ProjectConfigurationError,
        BuildMaxConcurrencyError,
        SoftTimeLimitExceeded,
    )

    # Do not send notifications on failure builds for these exceptions.
    exceptions_without_notifications = (
        BuildCancelled.CANCELLED_BY_USER,
        BuildCancelled.SKIPPED_EXIT_CODE_183,
        BuildAppError.BUILDS_DISABLED,
        BuildMaxConcurrencyError.LIMIT_REACHED,
    )

    # Do not send external build status on failure builds for these exceptions.
    exceptions_without_external_build_status = (BuildMaxConcurrencyError.LIMIT_REACHED,)

    acks_late = True
    track_started = True

    # These values have to be dynamic based on project
    time_limit = None
    soft_time_limit = None

    Request = BuildRequest

    def _setup_sigterm(self):
        def sigterm_received(*args, **kwargs):
            log.warning("SIGTERM received. Waiting for build to stop gracefully after it finishes.")

        def sigint_received(*args, **kwargs):
            log.warning("SIGINT received. Canceling the build running.")

            # Only allow to cancel the build if it's not already uploading the files.
            # This is to protect our users to end up with half of the documentation uploaded.
            # TODO: remove this condition once we implement "Atomic Uploads"
            if self.data.build.get("state") == BUILD_STATE_UPLOADING:
                log.warning('Ignoring cancelling the build at "Uploading" state.')
                return

            raise BuildCancelled(message_id=BuildCancelled.CANCELLED_BY_USER)

        # Do not send the SIGTERM signal to children (pip is automatically killed when
        # receives SIGTERM and make the build to fail one command and stop build)
        signal.signal(signal.SIGTERM, sigterm_received)

        signal.signal(signal.SIGINT, sigint_received)

    def _check_concurrency_limit(self):
        try:
            response = self.data.api_client.build.concurrent.get(
                project__slug=self.data.project.slug
            )
            concurrency_limit_reached = response.get("limit_reached", False)
            max_concurrent_builds = response.get(
                "max_concurrent",
                settings.RTD_MAX_CONCURRENT_BUILDS,
            )
        except Exception:
            log.exception(
                "Error while hitting/parsing API for concurrent limit checks from builder.",
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
                    BuildMaxConcurrencyError.LIMIT_REACHED,
                    format_values={
                        "limit": max_concurrent_builds,
                    },
                )
            )

    def _check_project_disabled(self):
        if self.data.project.skip:
            log.warning("Project build skipped.")
            raise BuildAppError(BuildAppError.BUILDS_DISABLED)

    def before_start(self, task_id, args, kwargs):
        # Create the object to store all the task-related data
        self.data = TaskData()

        # Comes from the signature of the task and they are the only
        # required arguments.
        self.data.version_pk, self.data.build_pk = args

        structlog.contextvars.bind_contextvars(build_id=self.data.build_pk)
        log.info("Running task.", name=self.name)

        self.data.start_time = timezone.now()
        self.data.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.data.environment_class = LocalBuildEnvironment

        self.data.api_client = setup_api(kwargs["build_api_key"])

        self.data.build = self.get_build(self.data.build_pk)
        self.data.version = self.get_version(self.data.version_pk)
        self.data.project = self.data.version.project

        # Save the builder instance's name into the build object
        self.data.build["builder"] = socket.gethostname()

        # Reset any previous build error reported to the user
        self.data.build["error"] = ""
        # Also note there are builds that are triggered without a commit
        # because they just build the latest commit for that version
        self.data.build_commit = kwargs.get("build_commit")

        self.data.build_director = BuildDirector(
            data=self.data,
        )

        structlog.contextvars.bind_contextvars(
            # NOTE: ``self.data.build`` is just a regular dict, not an APIBuild :'(
            builder=self.data.build["builder"],
            commit=self.data.build_commit,
            project_slug=self.data.project.slug,
            version_slug=self.data.version.slug,
        )

        # Log a warning if the task took more than 10 minutes to be retried
        if self.data.build["task_executed_at"]:
            task_executed_at = datetime.datetime.fromisoformat(self.data.build["task_executed_at"])
            delta = timezone.now() - task_executed_at
            if delta > timezone.timedelta(minutes=10):
                log.warning(
                    "This task waited more than 10 minutes to be retried.",
                    delta_minutes=round(delta.seconds / 60, 1),
                )

        # Save when the task was executed by a builder
        self.data.build["task_executed_at"] = timezone.now()

        # Enable scale-in protection on this instance
        #
        # TODO: move this to the beginning of this method
        # once we don't need to rely on `self.data.project`.
        if self.data.project.has_feature(Feature.SCALE_IN_PROTECTION):
            set_builder_scale_in_protection.delay(
                build_id=self.data.build_pk,
                builder=socket.gethostname(),
                protected_from_scale_in=True,
            )

        if self.data.project.has_feature(Feature.BUILD_FULL_CLEAN):
            # Clean DOCROOT path completely to avoid conflicts other projects
            clean_build()
        else:
            # Clean the build paths for this version to avoid conflicts with previous run
            clean_build(self.data.version)

        # NOTE: this is never called. I didn't find anything in the logs, so we
        # can probably remove it
        self._setup_sigterm()

        self._check_project_disabled()
        self._check_concurrency_limit()
        self._reset_build()

    def _reset_build(self):
        # Always reset the build before starting.
        # We used to only reset it when it has at least one command executed already.
        # However, with the introduction of the new notification system,
        # it could have a notification attached (e.g. Max concurrency build)
        # that needs to be removed from the build.
        # See https://github.com/readthedocs/readthedocs.org/issues/11131
        log.info("Resetting build.")
        self.data.api_client.build(self.data.build["id"]).reset.post()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Celery handler to be executed when a task fails.

        Updates build data, adds tasks to send build notifications.

        .. note::

           Since the task has failed, some attributes from the `self.data`
           object may not be defined.
        """
        log.info("Task failed.")
        if not self.data.build:
            # NOTE: use `self.data.build_id` (passed to the task) instead
            # `self.data.build` (retrieved from the API) because it's not present,
            # probably due the API failed when retrieving it.
            #
            # So, we create the `self.data.build` with the minimum required data.
            self.data.build = {
                "id": self.data.build_pk,
            }

        # Known errors in our application code (e.g. we couldn't connect to
        # Docker API). Report a generic message to the user.
        if isinstance(exc, BuildAppError):
            message_id = exc.message_id

        # Known errors in the user's project (e.g. invalid config file, invalid
        # repository, command failed, etc). Report the error back to the user
        # by creating a notification attached to the build
        # Otherwise, use a notification with a generic message.
        elif isinstance(exc, BuildUserError):
            if hasattr(exc, "message_id") and exc.message_id is not None:
                message_id = exc.message_id
            else:
                message_id = BuildUserError.GENERIC

            # Set build state as cancelled if the user cancelled the build
            if isinstance(exc, BuildCancelled):
                self.data.build["state"] = BUILD_STATE_CANCELLED

        elif isinstance(exc, SoftTimeLimitExceeded):
            log.info("Soft time limit exceeded.")
            message_id = BuildUserError.BUILD_TIME_OUT

        else:
            # We don't know what happened in the build. Log the exception and
            # report a generic notification to the user.
            # Note we are using `log.error(exc_info=...)` instead of `log.exception`
            # because this is not executed inside a try/except block.
            log.error("Build failed with unhandled exception.", exc_info=exc)
            message_id = BuildAppError.GENERIC_WITH_BUILD_ID

        # Grab the format values from the exception in case it contains
        format_values = exc.format_values if hasattr(exc, "format_values") else None

        # Attach the notification to the build, only when ``BuildDirector`` is available.
        # It may happens the director is not created because the API failed to retrieve
        # required data to initialize it on ``before_start``.
        if self.data.build_director:
            self.data.build_director.attach_notification(
                attached_to=f"build/{self.data.build['id']}",
                message_id=message_id,
                format_values=format_values,
            )
        else:
            log.warning(
                "We couldn't attach a notification to the build since it failed on an early stage."
            )

        # Send notifications for unhandled errors
        if message_id not in self.exceptions_without_notifications:
            self.send_notifications(
                self.data.version_pk,
                self.data.build["id"],
                event=WebHookEvent.BUILD_FAILED,
            )

        # NOTE: why we wouldn't have `self.data.build_commit` here?
        # This attribute is set when we get it after cloning the repository
        #
        # Oh, I think this is to differentiate a task triggered with
        # `Build.commit` than a one triggered just with the `Version` to build
        # the _latest_ commit of it
        if (
            self.data.build_commit
            and message_id not in self.exceptions_without_external_build_status
        ):
            version_type = None
            if self.data.version:
                version_type = self.data.version.type

            status = BUILD_STATUS_FAILURE
            if message_id == BuildCancelled.SKIPPED_EXIT_CODE_183:
                # The build was skipped by returning the magic exit code,
                # marked as CANCELLED, but communicated to GitHub as successful.
                # This is because the PR has to be available for merging when the build
                # was skipped on purpose.
                status = BUILD_STATUS_SUCCESS

            send_external_build_status(
                version_type=version_type,
                build_pk=self.data.build["id"],
                commit=self.data.build_commit,
                status=status,
            )

        # Update build object
        self.data.build["success"] = False

    def get_valid_artifact_types(self):
        """
        Return a list of all the valid artifact types for this build.

        It performs the following checks on each output format type path:
         - it exists
         - it is a directory
         - does not contains more than 1 files (only PDF, HTMLZip, ePUB)
         - it contains an "index.html" file at its root directory (only HTML)

        TODO: remove the limitation of only 1 file.
        Add support for multiple PDF files in the output directory and
        grab them by using glob syntax between other files that could be garbage.
        """
        valid_artifacts = []
        for artifact_type in ARTIFACT_TYPES:
            artifact_directory = self.data.project.artifact_path(
                version=self.data.version.slug,
                type_=artifact_type,
            )

            if artifact_type == "html":
                index_html_filepath = os.path.join(artifact_directory, "index.html")
                if not os.path.exists(index_html_filepath):
                    log.info(
                        "Failing the build. "
                        "HTML output does not contain an 'index.html' at its root directory.",
                        index_html=index_html_filepath,
                    )
                    raise BuildUserError(BuildUserError.BUILD_OUTPUT_HTML_NO_INDEX_FILE)

            if not os.path.exists(artifact_directory):
                # There is no output directory.
                # Skip this format.
                continue

            if not os.path.isdir(artifact_directory):
                log.debug(
                    "The output path is not a directory.",
                    output_format=artifact_type,
                )
                raise BuildUserError(
                    BuildUserError.BUILD_OUTPUT_IS_NOT_A_DIRECTORY,
                    format_values={
                        "artifact_type": artifact_type,
                    },
                )

            # Check if there are multiple files on artifact directories.
            # These output format does not support multiple files yet.
            # In case multiple files are found, the upload for this format is not performed.
            if artifact_type in ARTIFACT_TYPES_WITHOUT_MULTIPLE_FILES_SUPPORT:
                list_dir = os.listdir(artifact_directory)
                artifact_format_files = len(list_dir)
                if artifact_format_files > 1:
                    log.debug(
                        "Multiple files are not supported for this format. "
                        "Skipping this output format.",
                        output_format=artifact_type,
                    )
                    raise BuildUserError(
                        BuildUserError.BUILD_OUTPUT_HAS_MULTIPLE_FILES,
                        format_values={
                            "artifact_type": artifact_type,
                        },
                    )
                if artifact_format_files == 0:
                    raise BuildUserError(
                        BuildUserError.BUILD_OUTPUT_HAS_0_FILES,
                        format_values={
                            "artifact_type": artifact_type,
                        },
                    )

                # Rename file as "<project_slug>-<version_slug>.<artifact_type>",
                # which is the filename that Proxito serves for offline formats.
                filename = list_dir[0]
                _, extension = filename.rsplit(".")
                path = Path(artifact_directory) / filename
                destination = Path(artifact_directory) / f"{self.data.project.slug}.{extension}"
                assert_path_is_inside_docroot(path)
                assert_path_is_inside_docroot(destination)
                shutil.move(path, destination)

            # If all the conditions were met, the artifact is valid
            valid_artifacts.append(artifact_type)

        return valid_artifacts

    def on_success(self, retval, task_id, args, kwargs):
        valid_artifacts = self.get_valid_artifact_types()

        # NOTE: we are updating the db version instance *only* when
        # TODO: remove this condition and *always* update the DB Version instance
        if "html" in valid_artifacts:
            data = {
                "built": True,
                "documentation_type": self.data.version.documentation_type,
                "has_pdf": "pdf" in valid_artifacts,
                "has_epub": "epub" in valid_artifacts,
                "has_htmlzip": "htmlzip" in valid_artifacts,
                "build_data": self.data.version.build_data,
                "addons": self.data.version.addons,
            }
            # Update the latest version to point to the current VCS default branch
            # if the project doesn't have an explicit default branch set.
            if self.data.default_branch:
                data["identifier"] = self.data.default_branch
                data["type"] = BRANCH
            try:
                self.data.api_client.version(self.data.version.pk).patch(data)
            except HttpClientError:
                # NOTE: I think we should fail the build if we cannot update
                # the version at this point. Otherwise, we will have inconsistent data
                log.exception(
                    "Updating version db object failed. "
                    'Files are synced in the storage, but "Version" object is not updated',
                )

        # Index search data
        index_build.delay(build_id=self.data.build["id"])

        # Check if the project is spam
        if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.tasks import (  # noqa
                spam_check_after_build_complete,
            )

            spam_check_after_build_complete.delay(build_id=self.data.build["id"])

        if not self.data.project.has_valid_clone:
            self.set_valid_clone()

        self.send_notifications(
            self.data.version.pk,
            self.data.build["id"],
            event=WebHookEvent.BUILD_PASSED,
        )

        if self.data.build_commit:
            send_external_build_status(
                version_type=self.data.version.type,
                build_pk=self.data.build["id"],
                commit=self.data.build_commit,
                status=BUILD_STATUS_SUCCESS,
            )

        # Update build object
        self.data.build["success"] = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Celery helper called when the task is retried.

        This happens when any of the exceptions defined in ``autoretry_for``
        argument is raised or when ``self.retry`` is called from inside the
        task.

        See https://docs.celeryproject.org/en/master/userguide/tasks.html#retrying
        """
        log.info("Retrying this task.")

        if isinstance(exc, BuildMaxConcurrencyError):
            log.warning(
                "Delaying tasks due to concurrency limit.",
                project_slug=self.data.project.slug,
                version_slug=self.data.version.slug,
            )

            # Grab the format values from the exception in case it contains
            format_values = exc.format_values if hasattr(exc, "format_values") else None
            self.data.build_director.attach_notification(
                attached_to=f"build/{self.data.build['id']}",
                message_id=BuildMaxConcurrencyError.LIMIT_REACHED,
                format_values=format_values,
            )

        # Always update the build on retry
        self.update_build(state=BUILD_STATE_TRIGGERED)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Celery handler to be executed after a task runs.

        .. note::

           This handler is called even if the task has failed,
           so some attributes from the `self.data` object may not be defined.
        """
        # Update build object
        self.data.build["length"] = (timezone.now() - self.data.start_time).seconds

        build_state = None
        # The state key might not be defined
        # previous to finishing the task.
        if self.data.build.get("state") not in BUILD_FINAL_STATES:
            build_state = BUILD_STATE_FINISHED

        self.update_build(build_state)
        self.save_build_data()

        # Be defensive with the signal, so if a listener fails we still clean up
        try:
            build_complete.send(sender=Build, build=self.data.build)
        except Exception:
            log.exception("Error during build_complete", exc_info=True)

        if self.data.version:
            clean_build(self.data.version)

        try:
            self.data.api_client.revoke.post()
        except Exception:
            log.exception("Failed to revoke build api key.", exc_info=True)

        # Disable scale-in protection on this instance
        if self.data.project.has_feature(Feature.SCALE_IN_PROTECTION):
            set_builder_scale_in_protection.delay(
                build_id=self.data.build_pk,
                builder=socket.gethostname(),
                protected_from_scale_in=False,
            )

        log.info(
            "Build finished.",
            length=self.data.build["length"],
            success=self.data.build["success"],
        )

    def update_build(self, state=None):
        if state:
            self.data.build["state"] = state

        # Attempt to stop unicode errors on build reporting
        # for key, val in list(self.data.build.items()):
        #     if isinstance(val, bytes):
        #         self.data.build[key] = val.decode('utf-8', 'ignore')

        try:
            self.data.api_client.build(self.data.build["id"]).patch(self.data.build)
        except Exception:
            # NOTE: we are updating the "Build" object on each `state`.
            # Only if the last update fails, there may be some inconsistency
            # between the "Build" object in our db and the reality.
            #
            # The `state` argument will help us to track this more and understand
            # at what state our updates are failing and decide what to do.
            log.exception("Error while updating the build object.", state=state)

    def execute(self):
        # Cloning
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
                if getattr(self.data.config.build, "commands", False):
                    self.update_build(state=BUILD_STATE_INSTALLING)
                    self.data.build_director.install_build_tools()

                    self.update_build(state=BUILD_STATE_BUILDING)
                    self.data.build_director.run_build_commands()
                else:
                    # Installing
                    self.update_build(state=BUILD_STATE_INSTALLING)
                    self.data.build_director.setup_environment()

                    # Building
                    self.update_build(state=BUILD_STATE_BUILDING)
                    self.data.build_director.build()
            finally:
                self.data.build_director.check_old_output_directory()
                self.data.build_data = self.collect_build_data()

        # At this point, the user's build already succeeded.
        # However, we cannot use `.on_success()` because we still have to upload the artifacts;
        # which could fail, and we want to detect that and handle it properly at `.on_failure()`
        # Store build artifacts to storage (local or cloud storage)
        self.store_build_artifacts()

    def collect_build_data(self):
        """
        Collect data from the current build.

        The data is collected from inside the container,
        so this must be called before killing the container.
        """
        try:
            return BuildDataCollector(self.data.build_director.build_environment).collect()
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

    def get_build(self, build_pk):
        """
        Retrieve build object from API.

        :param build_pk: Build primary key
        """
        build = {}
        if build_pk:
            build = self.data.api_client.build(build_pk).get()
        private_keys = [
            "project",
            "version",
            "resource_uri",
            "absolute_uri",
        ]
        # TODO: try to use the same technique than for ``APIProject``.
        return {key: val for key, val in build.items() if key not in private_keys}

    # NOTE: this can be just updated on `self.data.build['']` and sent once the
    # build has finished to reduce API calls.
    def set_valid_clone(self):
        """Mark on the project that it has been cloned properly."""
        self.data.api_client.project(self.data.project.pk).patch({"has_valid_clone": True})
        self.data.project.has_valid_clone = True
        self.data.version.project.has_valid_clone = True

    def store_build_artifacts(self):
        """
        Save build artifacts to "storage" using Django's storage API.

        The storage could be local filesystem storage OR cloud blob storage
        such as S3, Azure storage or Google Cloud Storage.

        Remove build artifacts of types not included in this build (PDF, ePub, zip only).
        """
        time_before_store_build_artifacts = timezone.now()
        log.info("Writing build artifacts to media storage")
        self.update_build(state=BUILD_STATE_UPLOADING)

        valid_artifacts = self.get_valid_artifact_types()
        structlog.contextvars.bind_contextvars(artifacts=valid_artifacts)

        types_to_copy = []
        types_to_delete = []

        build_media_storage = get_storage(
            project=self.data.project,
            build_id=self.data.build["id"],
            api_client=self.data.api_client,
            storage_type=StorageType.build_media,
        )

        for artifact_type in ARTIFACT_TYPES:
            if artifact_type in valid_artifacts:
                types_to_copy.append(artifact_type)
            # Never delete HTML nor JSON (search index)
            elif artifact_type not in UNDELETABLE_ARTIFACT_TYPES:
                types_to_delete.append(artifact_type)

        # Upload formats
        for media_type in types_to_copy:
            from_path = self.data.project.artifact_path(
                version=self.data.version.slug,
                type_=media_type,
            )
            to_path = self.data.project.get_storage_path(
                type_=media_type,
                version_slug=self.data.version.slug,
                include_file=False,
                version_type=self.data.version.type,
            )

            self._log_directory_size(from_path, media_type)

            try:
                build_media_storage.rclone_sync_directory(from_path, to_path)
            except Exception as exc:
                # NOTE: the exceptions reported so far are:
                #  - botocore.exceptions:HTTPClientError
                #  - botocore.exceptions:ClientError
                #  - readthedocs.doc_builder.exceptions:BuildCancelled
                log.exception(
                    "Error copying to storage",
                    media_type=media_type,
                    from_path=from_path,
                    to_path=to_path,
                )
                # Re-raise the exception to fail the build and handle it
                # automatically at `on_failure`.
                # It will clearly communicate the error to the user.
                raise BuildAppError(
                    BuildAppError.UPLOAD_FAILED,
                    exception_message="Error uploading files to the storage.",
                ) from exc

        # Delete formats
        for media_type in types_to_delete:
            media_path = self.data.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.data.version.slug,
                include_file=False,
                version_type=self.data.version.type,
            )
            try:
                build_media_storage.delete_directory(media_path)
            except Exception as exc:
                # NOTE: I didn't find any log line for this case yet
                log.exception(
                    "Error deleting files from storage",
                    media_type=media_type,
                    media_path=media_path,
                )
                # Re-raise the exception to fail the build and handle it
                # automatically at `on_failure`.
                # It will clearly communicate the error to the user.
                raise BuildAppError(
                    BuildAppError.GENERIC_WITH_BUILD_ID,
                    exception_message="Error deleting files from storage.",
                ) from exc

        log.info(
            "Store build artifacts finished.",
            time=(timezone.now() - time_before_store_build_artifacts).seconds,
        )

    def _log_directory_size(self, directory, media_type):
        try:
            output = subprocess.check_output(["du", "--summarize", "-m", "--", directory])
            # The output is something like: "5\t/path/to/directory".
            directory_size = int(output.decode().split()[0])
            log.info(
                "Build artifacts directory size.",
                directory=directory,
                size=directory_size,  # Size in mega bytes
                media_type=media_type,
            )
        except Exception:
            log.info(
                "Error getting build artifacts directory size.",
                exc_info=True,
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
def update_docs_task(self, version_id, build_id, *, build_api_key, build_commit=None, **kwargs):
    # In case we pass more arguments than expected, log them and ignore them,
    # so we don't break builds while we deploy a change that requires an extra argument.
    if kwargs:
        log.warning("Extra arguments passed to update_docs_task", arguments=kwargs)
    self.execute()
