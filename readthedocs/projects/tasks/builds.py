"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""

import datetime
import json
import os
import shutil
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
from readthedocs.doc_builder.exceptions import (
    BuildEnvironmentError,
    BuildMaxConcurrencyError,
    BuildTimeoutError,
    DuplicatedBuildError,
    ProjectBuildsSkippedError,
    VersionLockedError,
    YAMLParseError,
)
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.search.utils import index_new_files, remove_indexed_files
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.storage import build_environment_storage, build_media_storage
from readthedocs.vcs_support.utils import LockTimeout
from readthedocs.worker import app


from ..exceptions import RepositoryError
from ..models import APIProject, Feature, WebHookEvent, HTMLFile, ImportedFile, Project
from ..signals import (
    after_build,
    before_build,
    before_vcs,
    files_changed,
)

from .base import BuildTaskBase
from .mixins import SyncRepositoryMixin
from .utils import clean_build

log = structlog.get_logger(__name__)


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
    # throws = [
    #     LockTimeout,
    #     RepositoryError,
    # ]

    # NOTE: not use the base task because it differs from the "update docs task" considerably
    # base = BuildTaskBase

    def before_start(self, task_id, args, kwargs):
        log.info('Running task.', name=self.name)

        # NOTE: save all the attributes to do a clean up when finish
        self._attributes = list(self.__dict__.keys()) + ['_attributes']

        version_id = kwargs.get('version_id')

        # load all data from the API required for the build
        self.version = self.get_version(version_id)
        self.project = self.version.project

        log.bind(
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )

        self.project.repo_nonblockinglock(version=self.version).acquire_lock()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Do not log as error handled exceptions
        if isinstance(exc, RepositoryError):
            log.warning(
                'There was an error with the repository.',
                exc_info=True,
            )
        elif isinstance(exc, LockTimeout):
            countdown = 120
            log.info(
                'Lock still active. Retrying this task with countdown delay...',
                countdown=countdown,
            )
            self.task.retry(
                exc=exc,
                throw=False,
                countdown=countdown,
            )
        else:
            # Catch unhandled errors when syncing
            log.exception('An unhandled exception was raised during VCS syncing.')

    def on_sucess(self, retval, task_id, args, kwargs):
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        pass

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        clean_build(self.version.pk)

        # unlock repository directory
        self.project.repo_nonblockinglock(version=self.version).release_lock()

        # HACK: cleanup all the attributes set by the task under `self`
        for attribute in list(self.__dict__.keys()):
            if attribute not in self._attributes:
                del self.__dict__[attribute]

    def execute(self):

        # import datetime
        # if datetime.datetime.now().minute == 41:
        #     raise LockTimeout

        environment = self.environment_class(
            project=self.project,
            version=self.version,
            record=False,
            update_on_success=False,
            environment=self.get_vcs_env_vars(),
        )

        with environment:
            before_vcs.send(
                sender=self.version,
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
                not self.project.has_feature(Feature.VCS_REMOTE_LISTING),
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
def sync_repository_task(self, version_id=None):
    # from celery.contrib import rdb; rdb.set_trace()

    # NOTE: `before_start` is new on Celery 5.2.x, but we are using 5.1.x currently.
    self.before_start(self.request.id, self.request.args, self.request.kwargs)

    self.execute()

# TODO: move `BuildTaskBase` into this task class because it's not reused by
# any other task.
class UpdateDocsTask(BuildTaskBase, SyncRepositoryMixin, Task):

    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported, we created
    it or a webhook is received. Then it will sync the repository and build the
    html docs if needed.
    """

    name = __name__ + '.update_docs_task'

    # NOTE: I think this __init__ is not required and it's only used for tests purposes
    # def __init__(
    #         self,
    #         build_env=None,
    #         python_env=None,
    #         config=None,
    #         force=False,
    #         build=None,
    #         project=None,
    #         version=None,
    #         commit=None,
    #         task=None,
    # ):
    #     self.build_env = build_env
    #     self.python_env = python_env
    #     self.build_force = force
    #     self.build = {}
    #     if build is not None:
    #         self.build = build
    #     self.version = {}
    #     if version is not None:
    #         self.version = version
    #     self.commit = commit
    #     self.project = {}
    #     if project is not None:
    #         self.project = project
    #     if config is not None:
    #         self.config = config
    #     self.task = task
    #     self.build_start_time = None
    #     # TODO: remove this
    #     self.setup_env = None

    def execute(self):
            # self, version_pk, build_pk=None, commit=None, record=True,
            # force=False, **__
        """
        Run a documentation sync n' build.

        This is fully wrapped in exception handling to account for a number of
        failure cases. We first run a few commands in a build environment,
        but do not report on environment success. This avoids a flicker on the
        build output page where the build is marked as finished in between the
        checkout steps and the build steps.

        Unhandled exceptions raise a generic user facing error, which directs
        the user to bug us. It is therefore a benefit to have as few unhandled
        errors as possible.

        :param version_pk int: Project Version id
        :param build_pk int: Build id (if None, commands are not recorded)
        :param commit: commit sha of the version required for sending build status reports
        :param record bool: record a build object in the database
        :param force bool: force Sphinx build
        """
        self.run_setup()
        self.run_build()

    def run_setup(self):
        """
        Run setup in a build environment.

        1. Create a Docker container with the default image
        2. Clone the repository's code and submodules
        3. Save the `config` object into the database
        """
        environment = self.environment_class(
            project=self.project,
            version=self.version,
            build=self.build,
            record=self,
            update_on_success=False,
            environment=self.get_vcs_env_vars(),
        )

        # NOTE: find the start time from the celery task itself
        self.build_start_time = environment.start_time

        # Environment used for code checkout & initial configuration reading
        with environment:
            before_vcs.send(
                sender=self.version,
                environment=environment,
            )

            self.setup_vcs(environment)
            self.config = load_yaml_config(version=self.version)
            self.save_build_config()
            self.update_vcs_submodules(environment)

    def update_vcs_submodules(self, environment):
        version_repo = self.get_vcs_repo(environment)
        if version_repo.supports_submodules:
            version_repo.update_submodules(self.config)

    def run_build(self):
        """
        Build the docs in an environment.

        """
        self.build_env = self.environment_class(
            project=self.project,
            version=self.version,
            config=self.config,
            build=self.build,
            record=self.record,
            environment=self.get_build_env_vars(),

            # NOTE: I think this is used only to calculate the length of the
            # build --we can use the Celery's task start time instead

            # Pass ``start_time`` here to not reset the timer
            start_time=self.build_start_time,
        )

        # Environment used for building code, usually with Docker
        with self.build_env:
            python_env_cls = Virtualenv
            if any([
                    self.config.conda is not None,
                    self.config.python_interpreter in ('conda', 'mamba'),
            ]):
                python_env_cls = Conda

            self.python_env = python_env_cls(
                version=self.version,
                build_env=self.build_env,
                config=self.config,
            )

            # TODO: check if `before_build` and `after_build` are still useful
            # (maybe in commercial?)
            before_build.send(
                sender=self.version,
                environment=self.build_env,
            )
            self.setup_build()
            self.build_docs()
            after_build.send(
                sender=self.version,
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
        if self.project.has_feature(Feature.UPDATE_CA_CERTIFICATES):
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

        commit = self.commit or self.get_vcs_repo(environment).commit
        if commit:
            self.build['commit'] = commit

    def get_build_env_vars(self):
        """Get bash environment variables used for all builder commands."""
        env = self.get_rtd_env_vars()

        # https://no-color.org/
        env['NO_COLOR'] = '1'

        if self.config.conda is not None:
            env.update({
                'CONDA_ENVS_PATH': os.path.join(self.project.doc_path, 'conda'),
                'CONDA_DEFAULT_ENV': self.version.slug,
                'BIN_PATH': os.path.join(
                    self.project.doc_path,
                    'conda',
                    self.version.slug,
                    'bin',
                ),
            })
        else:
            env.update({
                'BIN_PATH': os.path.join(
                    self.project.doc_path,
                    'envs',
                    self.version.slug,
                    'bin',
                ),
            })

        # Update environment from Project's specific environment variables,
        # avoiding to expose private environment variables
        # if the version is external (i.e. a PR build).
        env.update(self.project.environment_variables(
            public_only=self.version.is_external
        ))

        return env

    def set_valid_clone(self):
        """Mark on the project that it has been cloned properly."""
        api_v2.project(self.project.pk).patch(
            {'has_valid_clone': True}
        )
        self.project.has_valid_clone = True
        self.version.project.has_valid_clone = True

    # TODO: think about reducing the amount of API calls. Can we just save the
    # `config` in memory (`self.build['config']`) and update it later (e.g.
    # together with the build status)?
    def save_build_config(self):
        """Save config in the build object."""
        pk = self.build['id']
        config = self.config.as_dict()
        api_v2.build(pk).patch({
            'config': config,
        })
        self.build['config'] = config

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
            types_to_copy.append(('html', self.config.doctype))

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
            from_path = self.version.project.artifact_path(
                version=self.version.slug,
                type_=build_type,
            )
            to_path = self.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.version.slug,
                include_file=False,
                version_type=self.version.type,
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
            media_path = self.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.version.slug,
                include_file=False,
                version_type=self.version.type,
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
        self.install_system_dependencies()
        self.setup_python_environment()

    def setup_python_environment(self):
        """
        Build the virtualenv and install the project into it.

        Always build projects with a virtualenv.

        :param build_env: Build environment to pass commands and execution through.
        """
        self.update_build(state=BUILD_STATE_INSTALLING)

        # Install all ``build.tools`` specified by the user
        if self.config.using_build_tools:
            self.python_env.install_build_tools()

        self.python_env.setup_base()
        self.python_env.install_core_requirements()
        self.python_env.install_requirements()
        if self.project.has_feature(Feature.LIST_PACKAGES_INSTALLED_ENV):
            self.python_env.list_packages_installed()

    def install_system_dependencies(self):
        """
        Install apt packages from the config file.

        We don't allow to pass custom options or install from a path.
        The packages names are already validated when reading the config file.

        .. note::

           ``--quiet`` won't suppress the output,
           it would just remove the progress bar.
        """
        packages = self.config.build.apt_packages
        if packages:
            self.build_env.run(
                'apt-get', 'update', '--assume-yes', '--quiet',
                user=settings.RTD_DOCKER_SUPER_USER,
            )
            # put ``--`` to end all command arguments.
            self.build_env.run(
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

        self.outcomes = defaultdict(lambda: False)
        self.outcomes['html'] = self.build_docs_html()
        self.outcomes['search'] = self.build_docs_search()
        self.outcomes['localmedia'] = self.build_docs_localmedia()
        self.outcomes['pdf'] = self.build_docs_pdf()
        self.outcomes['epub'] = self.build_docs_epub()

        return self.outcomes

    def build_docs_html(self):
        """Build HTML docs."""
        html_builder = get_builder_class(self.config.doctype)(
            build_env=self.build_env,
            python_env=self.python_env,
        )
        if self.force:
            html_builder.force()
        html_builder.append_conf()
        success = html_builder.build()
        if success:
            html_builder.move()

        return success

    def get_final_doctype(self):
        html_builder = get_builder_class(self.config.doctype)(
            build_env=self.build_env,
            python_env=self.python_env,
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
            'htmlzip' not in self.config.formats or
            self.version.type == EXTERNAL
        ):
            return False
        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_singlehtmllocalmedia')
        return False

    def build_docs_pdf(self):
        """Build PDF docs."""
        if 'pdf' not in self.config.formats or self.version.type == EXTERNAL:
            return False
        # Mkdocs has no pdf generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_pdf')
        return False

    def build_docs_epub(self):
        """Build ePub docs."""
        if 'epub' not in self.config.formats or self.version.type == EXTERNAL:
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
            self.build_env,
            python_env=self.python_env,
        )
        success = builder.build()
        builder.move()
        return success

    def send_notifications(self, version_pk, build_pk, event):
        """Send notifications to all subscribers of `event`."""
        # Try to infer the version type if we can
        # before creating a task.
        if not self.version or self.version.type != EXTERNAL:
            build_tasks.send_build_notifications.delay(
                version_pk=version_pk,
                build_pk=build_pk,
                event=event,
            )

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return 'sphinx' in self.config.doctype


# TODO: rename this task to `build_task`
@app.task(
    base=UpdateDocsTask,
    bind=True,
)
def update_docs_task(self, *args, **kwargs):
    # from celery.contrib import rdb; rdb.set_trace()

    # HACK: just for now while we are developing the code
    self.request.kwargs['version_pk'] = args[0]

    # NOTE: `before_start` is new on Celery 5.2.x, but we are using 5.1.x currently.
    self.before_start(self.request.id, self.request.args, self.request.kwargs)

    self.execute()
