"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""

import datetime
import json
import os
import signal
import socket
import tarfile
import tempfile
from collections import Counter, defaultdict

from celery import Task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from slumber.exceptions import HttpClientError
from sphinx.ext import intersphinx

import structlog

from readthedocs.api.v2.client import api as api_v2
from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_INSTALLING,
    BUILD_STATE_UPLOADING,
    BUILD_STATUS_FAILURE,
    BUILD_STATUS_SUCCESS,
    EXTERNAL,
    LATEST_VERBOSE_NAME,
    STABLE_VERBOSE_NAME,
)
from readthedocs.builds.models import APIVersion, Build, Version
from readthedocs.builds.signals import build_complete
from readthedocs.config import ConfigError
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import (
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import (
    BuildAppError,
    BuildUserError,
    BuildMaxConcurrencyError,
    DuplicatedBuildError,
    ProjectBuildsSkippedError,
    YAMLParseError,
)
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.search.utils import index_new_files, remove_indexed_files
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.storage import build_environment_storage, build_media_storage
from readthedocs.worker import app


from ..exceptions import RepositoryError
from ..models import APIProject, Feature, WebHookEvent, HTMLFile, ImportedFile, Project
from ..signals import (
    after_build,
    before_build,
    before_vcs,
    files_changed,
)

from .mixins import SyncRepositoryMixin
from .utils import clean_build, BuildRequest, send_external_build_status
from .search import fileify

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

    pass


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

        log.bind(
            project_slug=self.data.project.slug,
            version_slug=self.data.version.slug,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Do not log as error handled exceptions
        if isinstance(exc, RepositoryError):
            log.warning(
                'There was an error with the repository.',
                exc_info=True,
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
            environment=self.get_vcs_env_vars(),
        )

        with environment:
            before_vcs.send(
                sender=self.data.version,
                environment=environment,
            )
            self.update_versions_from_repository(environment)

    def update_versions_from_repository(self, environment):
        """
        Update Read the Docs versions from VCS repository.

        Depending if the VCS backend supports remote listing, we just list its branches/tags
        remotely or we do a full clone and local listing of branches/tags.
        """
        version_repo = self.get_vcs_repo(environment)
        if any([
                not version_repo.supports_lsremote,
                not self.data.project.has_feature(Feature.VCS_REMOTE_LISTING),
        ]):
            log.info('Syncing repository via full clone.')
            self.sync_repo(environment)
        else:
            log.info('Syncing repository via remote listing.')
            self.sync_versions(version_repo)


@app.task(
    base=SyncRepositoryTask,
    bind=True,
)
def sync_repository_task(self, version_id):
    # NOTE: `before_start` is new on Celery 5.2.x, but we are using 5.1.x currently.
    self.before_start(self.request.id, self.request.args, self.request.kwargs)

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
    max_retries = 5  # 5 per normal builds, 25 per concurrency limited
    default_retry_delay = 7 * 60

    # Expected exceptions that will be logged as info only and not retried
    throws = (
        DuplicatedBuildError,
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

    def _setup_sigterm(self):
        def sigterm_received(*args, **kwargs):
            log.warning('SIGTERM received. Waiting for build to stop gracefully after it finishes.')

        # Do not send the SIGTERM signal to children (pip is automatically killed when
        # receives SIGTERM and make the build to fail one command and stop build)
        signal.signal(signal.SIGTERM, sigterm_received)

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
            # TODO: this could be handled in `on_retry` probably
            log.warning(
                'Delaying tasks due to concurrency limit.',
                project_slug=self.data.project.slug,
                version_slug=self.data.version.slug,
            )

            # This is done automatically on the environment context, but
            # we are executing this code before creating one
            api_v2.build(self.data.build['id']).patch({
                'error': BuildMaxConcurrencyError.message.format(
                    limit=max_concurrent_builds,
                ),
                'builder': socket.gethostname(),
            })
            self.retry(
                exc=BuildMaxConcurrencyError,
                throw=False,
                # We want to retry this build more times
                max_retries=25,
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
        log.info('Running task.', name=self.name)

        # Create the object to store all the task-related data
        self.data = TaskData()

        self.data.start_time = timezone.now()
        self.data.environment_class = DockerBuildEnvironment
        if not settings.DOCKER_ENABLE:
            # TODO: delete LocalBuildEnvironment since it's not supported
            # anymore and we are not using it
            self.data.environment_class = LocalBuildEnvironment

        # Comes from the signature of the task and they are the only required
        # arguments
        self.data.version_pk, self.data.build_pk = args

        self.data.build = self.get_build(self.data.build_pk)
        self.data.version = self.get_version(self.data.version_pk)
        self.data.project = self.data.version.project

        # Save the builder instance's name into the build object
        self.data.build['builder'] = socket.gethostname()

        # Also note there are builds that are triggered without a commit
        # because they just build the latest commit for that version
        self.data.build_commit = kwargs.get('build_commit')

        log.bind(
            # NOTE: ``self.data.build`` is just a regular dict, not an APIBuild :'(
            build_id=self.data.build['id'],
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
        if self.data.build.get('commands'):
            api_v2.build(self.data.build['id']).reset.post()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
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
        if self.data.build_commit:
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
            self.data.build_env,
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
                api_v2.version(self.data.version.pk).patch({
                    'built': True,
                    'documentation_type': self.get_final_doctype(),
                    'has_pdf': pdf,
                    'has_epub': epub,
                    'has_htmlzip': localmedia,
                })
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
        log.warning('Retrying this task.')

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # Update build object
        self.data.build['length'] = (timezone.now() - self.data.start_time).seconds

        self.update_build(BUILD_STATE_FINISHED)

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
        self.run_setup()
        self.run_build()

    def run_setup(self):
        """
        Run setup in a build environment.

        1. Create a Docker container with the default image
        2. Clone the repository's code and submodules
        3. Save the `config` object into the database
        4. Update VCS submodules
        """
        environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            build=self.data.build,
            environment=self.get_vcs_env_vars(),
        )

        # Environment used for code checkout & initial configuration reading
        with environment:
            before_vcs.send(
                sender=self.data.version,
                environment=environment,
            )

            self.setup_vcs(environment)
            self.data.config = load_yaml_config(version=self.data.version)
            self.save_build_config()
            self.update_vcs_submodules(environment)

    def update_vcs_submodules(self, environment):
        version_repo = self.get_vcs_repo(environment)
        if version_repo.supports_submodules:
            version_repo.update_submodules(self.data.config)

    def run_build(self):
        """Build the docs in an environment."""
        self.data.build_env = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            config=self.data.config,
            build=self.data.build,
            environment=self.get_build_env_vars(),
        )

        # Environment used for building code, usually with Docker
        with self.data.build_env:
            python_env_cls = Virtualenv
            if any([
                    self.data.config.conda is not None,
                    self.data.config.python_interpreter in ('conda', 'mamba'),
            ]):
                python_env_cls = Conda

            self.data.python_env = python_env_cls(
                version=self.data.version,
                build_env=self.data.build_env,
                config=self.data.config,
            )

            # TODO: check if `before_build` and `after_build` are still useful
            # (maybe in commercial?)
            #
            # I didn't find they are used anywhere, we should probably remove them
            before_build.send(
                sender=self.data.version,
                environment=self.data.build_env,
            )

            self.setup_build()
            self.build_docs()

            after_build.send(
                sender=self.data.version,
            )

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

    def setup_vcs(self, environment):
        """
        Update the checkout of the repo to make sure it's the latest.

        This also syncs versions in the DB.
        """
        self.update_build(state=BUILD_STATE_CLONING)

        # Install a newer version of ca-certificates packages because it's
        # required for Let's Encrypt certificates
        # https://github.com/readthedocs/readthedocs.org/issues/8555
        # https://community.letsencrypt.org/t/openssl-client-compatibility-changes-for-let-s-encrypt-certificates/143816
        # TODO: remove this when a newer version of ``ca-certificates`` gets
        # pre-installed in the Docker images
        if self.data.project.has_feature(Feature.UPDATE_CA_CERTIFICATES):
            environment.run(
                'apt-get', 'update', '--assume-yes', '--quiet',
                user=settings.RTD_DOCKER_SUPER_USER,
                record=False,
            )
            environment.run(
                'apt-get', 'install', '--assume-yes', '--quiet', 'ca-certificates',
                user=settings.RTD_DOCKER_SUPER_USER,
                record=False,
            )

        self.sync_repo(environment)

        commit = self.data.build_commit or self.get_vcs_repo(environment).commit
        if commit:
            self.data.build['commit'] = commit

    def get_build_env_vars(self):
        """Get bash environment variables used for all builder commands."""
        env = self.get_rtd_env_vars()

        # https://no-color.org/
        env['NO_COLOR'] = '1'

        if self.data.config.conda is not None:
            env.update({
                'CONDA_ENVS_PATH': os.path.join(self.data.project.doc_path, 'conda'),
                'CONDA_DEFAULT_ENV': self.data.version.slug,
                'BIN_PATH': os.path.join(
                    self.data.project.doc_path,
                    'conda',
                    self.data.version.slug,
                    'bin',
                ),
            })
        else:
            env.update({
                'BIN_PATH': os.path.join(
                    self.data.project.doc_path,
                    'envs',
                    self.data.version.slug,
                    'bin',
                ),
            })

        # Update environment from Project's specific environment variables,
        # avoiding to expose private environment variables
        # if the version is external (i.e. a PR build).
        env.update(self.data.project.environment_variables(
            public_only=self.data.version.is_external
        ))

        return env

    # NOTE: this can be just updated on `self.data.build['']` and sent once the
    # build has finished to reduce API calls.
    def set_valid_clone(self):
        """Mark on the project that it has been cloned properly."""
        api_v2.project(self.data.project.pk).patch(
            {'has_valid_clone': True}
        )
        self.data.project.has_valid_clone = True
        self.data.version.project.has_valid_clone = True

    # TODO: think about reducing the amount of API calls. Can we just save the
    # `config` in memory (`self.data.build['config']`) and update it later (e.g.
    # together with the build status)?
    def save_build_config(self):
        """Save config in the build object."""
        pk = self.data.build['id']
        config = self.data.config.as_dict()
        api_v2.build(pk).patch({
            'config': config,
        })
        self.data.build['config'] = config

    def store_build_artifacts(
            self,
            environment,
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

    def setup_build(self):
        self.update_build(state=BUILD_STATE_INSTALLING)

        self.install_system_dependencies()
        self.setup_python_environment()

    def setup_python_environment(self):
        """
        Build the virtualenv and install the project into it.

        Always build projects with a virtualenv.

        :param build_env: Build environment to pass commands and execution through.
        """
        # Install all ``build.tools`` specified by the user
        if self.data.config.using_build_tools:
            self.data.python_env.install_build_tools()

        self.data.python_env.setup_base()
        self.data.python_env.install_core_requirements()
        self.data.python_env.install_requirements()
        if self.data.project.has_feature(Feature.LIST_PACKAGES_INSTALLED_ENV):
            self.data.python_env.list_packages_installed()

    def install_system_dependencies(self):
        """
        Install apt packages from the config file.

        We don't allow to pass custom options or install from a path.
        The packages names are already validated when reading the config file.

        .. note::

           ``--quiet`` won't suppress the output,
           it would just remove the progress bar.
        """
        packages = self.data.config.build.apt_packages
        if packages:
            self.data.build_env.run(
                'apt-get', 'update', '--assume-yes', '--quiet',
                user=settings.RTD_DOCKER_SUPER_USER,
            )
            # put ``--`` to end all command arguments.
            self.data.build_env.run(
                'apt-get', 'install', '--assume-yes', '--quiet', '--', *packages,
                user=settings.RTD_DOCKER_SUPER_USER,
            )

    def build_docs(self):
        """
        Wrapper to all build functions.

        Executes the necessary builds for this task and returns whether the
        build was successful or not.

        :returns: Build outcomes with keys for html, search, localmedia, pdf,
                  and epub
        :rtype: dict
        """
        self.update_build(state=BUILD_STATE_BUILDING)

        self.data.outcomes = defaultdict(lambda: False)
        self.data.outcomes['html'] = self.build_docs_html()
        self.data.outcomes['search'] = self.build_docs_search()
        self.data.outcomes['localmedia'] = self.build_docs_localmedia()
        self.data.outcomes['pdf'] = self.build_docs_pdf()
        self.data.outcomes['epub'] = self.build_docs_epub()

        return self.data.outcomes

    def build_docs_html(self):
        """Build HTML docs."""
        html_builder = get_builder_class(self.data.config.doctype)(
            build_env=self.data.build_env,
            python_env=self.data.python_env,
        )
        html_builder.append_conf()
        success = html_builder.build()
        if success:
            html_builder.move()

        return success

    def get_final_doctype(self):
        html_builder = get_builder_class(self.data.config.doctype)(
            build_env=self.data.build_env,
            python_env=self.data.python_env,
        )
        return html_builder.get_final_doctype()

    def build_docs_search(self):
        """
        Build search data.

        .. note::
           For MkDocs search is indexed from its ``html`` artifacts.
           And in sphinx is run using the rtd-sphinx-extension.
        """
        return self.is_type_sphinx()

    def build_docs_localmedia(self):
        """Get local media files with separate build."""
        if (
            'htmlzip' not in self.data.config.formats or
            self.data.version.type == EXTERNAL
        ):
            return False
        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_singlehtmllocalmedia')
        return False

    def build_docs_pdf(self):
        """Build PDF docs."""
        if 'pdf' not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False
        # Mkdocs has no pdf generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_pdf')
        return False

    def build_docs_epub(self):
        """Build ePub docs."""
        if 'epub' not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False
        # Mkdocs has no epub generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_epub')
        return False

    def build_docs_class(self, builder_class):
        """
        Build docs with additional doc backends.

        These steps are not necessarily required for the build to halt, so we
        only raise a warning exception here. A hard error will halt the build
        process.
        """
        builder = get_builder_class(builder_class)(
            self.data.build_env,
            python_env=self.data.python_env,
        )
        success = builder.build()
        builder.move()
        return success

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

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return 'sphinx' in self.data.config.doctype


@app.task(
    base=UpdateDocsTask,
    bind=True,
)
def update_docs_task(self, version_id, build_id, build_commit=None):
    # NOTE: `before_start` is new on Celery 5.2.x, but we are using 5.1.x currently.
    self.before_start(self.request.id, self.request.args, self.request.kwargs)

    self.execute()
