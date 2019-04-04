"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""

import datetime
import fnmatch
import hashlib
import json
import logging
import os
import shutil
import socket
from collections import Counter, defaultdict

import requests
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from slumber.exceptions import HttpClientError
from sphinx.ext import intersphinx


from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_INSTALLING,
    LATEST,
    LATEST_VERBOSE_NAME,
    STABLE_VERBOSE_NAME,
)
from readthedocs.builds.models import APIVersion, Build, Version
from readthedocs.builds.signals import build_complete
from readthedocs.builds.syncers import Syncer
from readthedocs.config import ConfigError
from readthedocs.core.resolver import resolve_path
from readthedocs.core.symlink import PrivateSymlink, PublicSymlink
from readthedocs.core.utils import broadcast, safe_unlink, send_email
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.doc_builder.environments import (
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import (
    BuildEnvironmentError,
    BuildEnvironmentWarning,
    BuildTimeoutError,
    MkDocsYAMLParseError,
    ProjectBuildsSkippedError,
    VersionLockedError,
    YAMLParseError,
)
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.projects.models import APIProject
from readthedocs.restapi.client import api as api_v2
from readthedocs.vcs_support import utils as vcs_support_utils
from readthedocs.worker import app

from .constants import LOG_TEMPLATE
from .exceptions import ProjectConfigurationError, RepositoryError
from .models import Domain, HTMLFile, ImportedFile, Project
from .signals import (
    after_build,
    after_vcs,
    before_build,
    before_vcs,
    bulk_post_create,
    bulk_post_delete,
    domain_verify,
    files_changed,
)


log = logging.getLogger(__name__)
storage = get_storage_class()()


class SyncRepositoryMixin:

    """Mixin that handles the VCS sync/update."""

    @staticmethod
    def get_version(project=None, version_pk=None):
        """
        Retrieve version data from the API.

        :param project: project object to sync
        :type project: projects.models.Project
        :param version_pk: version pk to sync
        :type version_pk: int
        :returns: a data-complete version object
        :rtype: builds.models.APIVersion
        """
        if not (project or version_pk):
            raise ValueError('project or version_pk is needed')
        if version_pk:
            version_data = api_v2.version(version_pk).get()
        else:
            version_data = (
                api_v2.version(project.slug).get(slug=LATEST)['objects'][0]
            )
        return APIVersion(**version_data)

    def get_vcs_repo(self):
        """Get the VCS object of the current project."""
        version_repo = self.project.vcs_repo(
            self.version.slug,
            # When called from ``SyncRepositoryTask.run`` we don't have
            # a ``setup_env`` so we use just ``None`` and commands won't
            # be recorded
            getattr(self, 'setup_env', None),
        )
        return version_repo

    def sync_repo(self):
        """Update the project's repository and hit ``sync_versions`` API."""
        # Make Dirs
        if not os.path.exists(self.project.doc_path):
            os.makedirs(self.project.doc_path)

        if not self.project.vcs_repo():
            raise RepositoryError(
                _('Repository type "{repo_type}" unknown').format(
                    repo_type=self.project.repo_type,
                ),
            )

        with self.project.repo_nonblockinglock(version=self.version):
            # Get the actual code on disk
            try:
                before_vcs.send(sender=self.version)
                msg = 'Checking out version {slug}: {identifier}'.format(
                    slug=self.version.slug,
                    identifier=self.version.identifier,
                )
                log.info(
                    LOG_TEMPLATE.format(
                        project=self.project.slug,
                        version=self.version.slug,
                        msg=msg,
                    ),
                )
                version_repo = self.get_vcs_repo()
                version_repo.update()
                self.sync_versions(version_repo)
                version_repo.checkout(self.version.identifier)
            finally:
                after_vcs.send(sender=self.version)

    def sync_versions(self, version_repo):
        """
        Update tags/branches hitting the API.

        It may trigger a new build to the stable version when hittig the
        ``sync_versions`` endpoint.
        """
        version_post_data = {'repo': version_repo.repo_url}

        if version_repo.supports_tags:
            version_post_data['tags'] = [{
                'identifier': v.identifier,
                'verbose_name': v.verbose_name,
            } for v in version_repo.tags]

        if version_repo.supports_branches:
            version_post_data['branches'] = [{
                'identifier': v.identifier,
                'verbose_name': v.verbose_name,
            } for v in version_repo.branches]

        self.validate_duplicate_reserved_versions(version_post_data)

        try:
            api_v2.project(self.project.pk).sync_versions.post(
                version_post_data,
            )
        except HttpClientError:
            log.exception('Sync Versions Exception')
        except Exception:
            log.exception('Unknown Sync Versions Exception')

    def validate_duplicate_reserved_versions(self, data):
        """
        Check if there are duplicated names of reserved versions.

        The user can't have a branch and a tag with the same name of
        ``latest`` or ``stable``. Raise a RepositoryError exception
        if there is a duplicated name.

        :param data: Dict containing the versions from tags and branches
        """
        version_names = [
            version['verbose_name']
            for version in data.get('tags', []) + data.get('branches', [])
        ]
        counter = Counter(version_names)
        for reserved_name in [STABLE_VERBOSE_NAME, LATEST_VERBOSE_NAME]:
            if counter[reserved_name] > 1:
                raise RepositoryError(
                    RepositoryError.DUPLICATED_RESERVED_VERSIONS,
                )


@app.task(max_retries=5, default_retry_delay=7 * 60)
def sync_repository_task(version_pk):
    """Celery task to trigger VCS version sync."""
    step = SyncRepositoryTaskStep()
    return step.run(version_pk)


class SyncRepositoryTaskStep(SyncRepositoryMixin):

    """
    Entry point to synchronize the VCS documentation.

    .. note::

        This is implemented as a separate class to isolate each run of the
        underlying task. Previously, we were using a custom ``celery.Task`` for
        this, but this class is only instantiated once -- on startup. The effect
        was that this instance shared state between workers.
    """

    def run(self, version_pk):  # pylint: disable=arguments-differ
        """
        Run the VCS synchronization.

        :param version_pk: version pk to sync
        :type version_pk: int
        :returns: whether or not the task ended successfully
        :rtype: bool
        """
        try:
            self.version = self.get_version(version_pk=version_pk)
            self.project = self.version.project
            self.sync_repo()
            return True
        except RepositoryError:
            # Do not log as ERROR handled exceptions
            log.warning('There was an error with the repository', exc_info=True)
        except vcs_support_utils.LockTimeout:
            log.info(
                'Lock still active: project=%s version=%s',
                self.project.slug,
                self.version.slug,
            )
        except Exception:
            # Catch unhandled errors when syncing
            log.exception(
                'An unhandled exception was raised during VCS syncing',
                extra={
                    'stack': True,
                    'tags': {
                        'project': self.project.slug,
                        'version': self.version.slug,
                    },
                },
            )
        return False


# Exceptions under ``throws`` argument are considered ERROR from a Build
# perspective (the build failed and can continue) but as a WARNING for the
# application itself (RTD code didn't failed). These exception are logged as
# ``INFO`` and they are not sent to Sentry.
@app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=7 * 60,
    throws=(
        VersionLockedError,
        ProjectBuildsSkippedError,
        YAMLParseError,
        BuildTimeoutError,
        BuildEnvironmentWarning,
        RepositoryError,
        ProjectConfigurationError,
        ProjectBuildsSkippedError,
        MkDocsYAMLParseError,
    ),
)
def update_docs_task(self, project_id, *args, **kwargs):
    step = UpdateDocsTaskStep(task=self)
    return step.run(project_id, *args, **kwargs)


class UpdateDocsTaskStep(SyncRepositoryMixin):

    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported, we created
    it or a webhook is received. Then it will sync the repository and build the
    html docs if needed.

    .. note::

        This is implemented as a separate class to isolate each run of the
        underlying task. Previously, we were using a custom ``celery.Task`` for
        this, but this class is only instantiated once -- on startup. The effect
        was that this instance shared state between workers.
    """

    def __init__(
            self,
            build_env=None,
            python_env=None,
            config=None,
            force=False,
            build=None,
            project=None,
            version=None,
            task=None,
    ):
        self.build_env = build_env
        self.python_env = python_env
        self.build_force = force
        self.build = {}
        if build is not None:
            self.build = build
        self.version = {}
        if version is not None:
            self.version = version
        self.project = {}
        if project is not None:
            self.project = project
        if config is not None:
            self.config = config
        self.task = task
        self.setup_env = None

    # pylint: disable=arguments-differ
    def run(
            self, pk, version_pk=None, build_pk=None, record=True, docker=None,
            force=False, **__
    ):
        """
        Run a documentation sync n' build.

        This is fully wrapped in exception handling to account for a number of
        failure cases. We first run a few commands in a local build environment,
        but do not report on environment success. This avoids a flicker on the
        build output page where the build is marked as finished in between the
        local environment steps and the docker build steps.

        If a failure is raised, or the build is not successful, return
        ``False``, otherwise, ``True``.

        Unhandled exceptions raise a generic user facing error, which directs
        the user to bug us. It is therefore a benefit to have as few unhandled
        errors as possible.

        :param pk int: Project id
        :param version_pk int: Project Version id (latest if None)
        :param build_pk int: Build id (if None, commands are not recorded)
        :param record bool: record a build object in the database
        :param docker bool: use docker to build the project (if ``None``,
            ``settings.DOCKER_ENABLE`` is used)
        :param force bool: force Sphinx build

        :returns: whether build was successful or not

        :rtype: bool
        """
        try:
            if docker is None:
                docker = settings.DOCKER_ENABLE

            self.project = self.get_project(pk)
            self.version = self.get_version(self.project, version_pk)
            self.build = self.get_build(build_pk)
            self.build_force = force
            self.config = None

            setup_successful = self.run_setup(record=record)
            if not setup_successful:
                return False

        # Catch unhandled errors in the setup step
        except Exception as e:  # noqa
            log.exception(
                'An unhandled exception was raised during build setup',
                extra={
                    'stack': True,
                    'tags': {
                        'build': build_pk,
                        # We can't depend on these objects because the api
                        # could fail. But self.project and self.version are
                        # initialized as empty dicts in the init method.
                        'project': self.project.slug if self.project else None,
                        'version': self.version.slug if self.version else None,
                    },
                },
            )
            if self.setup_env is not None:
                self.setup_env.failure = BuildEnvironmentError(
                    BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                        build_id=build_pk,
                    ),
                )
                self.setup_env.update_build(BUILD_STATE_FINISHED)

            # Send notifications for unhandled errors
            self.send_notifications()
            return False
        else:
            # No exceptions in the setup step, catch unhandled errors in the
            # build steps
            try:
                self.run_build(docker=docker, record=record)
            except Exception as e:  # noqa
                log.exception(
                    'An unhandled exception was raised during project build',
                    extra={
                        'stack': True,
                        'tags': {
                            'build': build_pk,
                            'project': self.project.slug,
                            'version': self.version.slug,
                        },
                    },
                )
                if self.build_env is not None:
                    self.build_env.failure = BuildEnvironmentError(
                        BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                            build_id=build_pk,
                        ),
                    )
                    self.build_env.update_build(BUILD_STATE_FINISHED)

                # Send notifications for unhandled errors
                self.send_notifications()
                return False

        return True

    def run_setup(self, record=True):
        """
        Run setup in the local environment.

        Return True if successful.
        """
        self.setup_env = LocalBuildEnvironment(
            project=self.project,
            version=self.version,
            build=self.build,
            record=record,
            update_on_success=False,
        )

        # Environment used for code checkout & initial configuration reading
        with self.setup_env:
            if self.project.skip:
                raise ProjectBuildsSkippedError
            try:
                self.setup_vcs()
            except vcs_support_utils.LockTimeout as e:
                self.task.retry(exc=e, throw=False)
                raise VersionLockedError
            try:
                self.config = load_yaml_config(version=self.version)
            except ConfigError as e:
                raise YAMLParseError(
                    YAMLParseError.GENERIC_WITH_PARSE_EXCEPTION.format(
                        exception=str(e),
                    ),
                )

            self.save_build_config()
            self.additional_vcs_operations()

        if self.setup_env.failure or self.config is None:
            msg = 'Failing build because of setup failure: {}'.format(
                self.setup_env.failure,
            )
            log.info(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg=msg,
                ),
            )

            # Send notification to users only if the build didn't fail because
            # of VersionLockedError: this exception occurs when a build is
            # triggered before the previous one has finished (e.g. two webhooks,
            # one after the other)
            if not isinstance(self.setup_env.failure, VersionLockedError):
                self.send_notifications()

            return False

        if self.setup_env.successful and not self.project.has_valid_clone:
            self.set_valid_clone()

        return True

    def additional_vcs_operations(self):
        """
        Execution of tasks that involve the project's VCS.

        All this tasks have access to the configuration object.
        """
        version_repo = self.get_vcs_repo()
        if version_repo.supports_submodules:
            version_repo.update_submodules(self.config)

    def run_build(self, docker, record):
        """
        Build the docs in an environment.

        :param docker: if ``True``, the build uses a ``DockerBuildEnvironment``,
            otherwise it uses a ``LocalBuildEnvironment`` to run all the
            commands to build the docs
        :param record: whether or not record all the commands in the ``Build``
            instance
        """
        env_vars = self.get_env_vars()

        if docker:
            env_cls = DockerBuildEnvironment
        else:
            env_cls = LocalBuildEnvironment
        self.build_env = env_cls(
            project=self.project,
            version=self.version,
            config=self.config,
            build=self.build,
            record=record,
            environment=env_vars,
        )

        # Environment used for building code, usually with Docker
        with self.build_env:
            python_env_cls = Virtualenv
            if self.config.conda is not None:
                log.info(
                    LOG_TEMPLATE.format(
                        project=self.project.slug,
                        version=self.version.slug,
                        msg='Using conda',
                    ),
                )
                python_env_cls = Conda
            self.python_env = python_env_cls(
                version=self.version,
                build_env=self.build_env,
                config=self.config,
            )

            try:
                self.setup_python_environment()

                # TODO the build object should have an idea of these states,
                # extend the model to include an idea of these outcomes
                outcomes = self.build_docs()
                build_id = self.build.get('id')
            except vcs_support_utils.LockTimeout as e:
                self.task.retry(exc=e, throw=False)
                raise VersionLockedError
            except SoftTimeLimitExceeded:
                raise BuildTimeoutError

            # Finalize build and update web servers
            if build_id:
                self.update_app_instances(
                    html=bool(outcomes['html']),
                    search=bool(outcomes['search']),
                    localmedia=bool(outcomes['localmedia']),
                    pdf=bool(outcomes['pdf']),
                    epub=bool(outcomes['epub']),
                )
            else:
                log.warning('No build ID, not syncing files')

        if self.build_env.failed:
            self.send_notifications()

        build_complete.send(sender=Build, build=self.build_env.build)

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
        return {
            key: val
            for key, val in build.items() if key not in private_keys
        }

    def setup_vcs(self):
        """
        Update the checkout of the repo to make sure it's the latest.

        This also syncs versions in the DB.
        """
        self.setup_env.update_build(state=BUILD_STATE_CLONING)

        log.info(
            LOG_TEMPLATE.format(
                project=self.project.slug,
                version=self.version.slug,
                msg='Updating docs from VCS',
            ),
        )
        try:
            self.sync_repo()
        except RepositoryError:
            log.warning('There was an error with the repository', exc_info=True)
            # Re raise the exception to stop the build at this point
            raise
        except vcs_support_utils.LockTimeout:
            log.info(
                'Lock still active: project=%s version=%s',
                self.project.slug,
                self.version.slug,
            )
            # Raise the proper exception (won't be sent to Sentry)
            raise VersionLockedError
        except Exception:
            # Catch unhandled errors when syncing
            log.exception(
                'An unhandled exception was raised during VCS syncing',
                extra={
                    'stack': True,
                    'tags': {
                        'build': self.build['id'],
                        'project': self.project.slug,
                        'version': self.version.slug,
                    },
                },
            )
            # Re raise the exception to stop the build at this point
            raise

        commit = self.project.vcs_repo(self.version.slug).commit
        if commit:
            self.build['commit'] = commit

    def get_env_vars(self):
        """Get bash environment variables used for all builder commands."""
        env = {
            'READTHEDOCS': True,
            'READTHEDOCS_VERSION': self.version.slug,
            'READTHEDOCS_PROJECT': self.project.slug,
        }

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

        # Update environment from Project's specific environment variables
        env.update(self.project.environment_variables)

        return env

    def set_valid_clone(self):
        """Mark on the project that it has been cloned properly."""
        api_v2.project(self.project.pk).patch(
            {'has_valid_clone': True}
        )
        self.project.has_valid_clone = True
        self.version.project.has_valid_clone = True

    def save_build_config(self):
        """Save config in the build object."""
        pk = self.build['id']
        config = self.config.as_dict()
        api_v2.build(pk).patch({
            'config': config,
        })
        self.build['config'] = config

    def update_app_instances(
            self,
            html=False,
            localmedia=False,
            search=False,
            pdf=False,
            epub=False,
    ):
        """
        Update application instances with build artifacts.

        This triggers updates across application instances for html, pdf, epub,
        downloads, and search. Tasks are broadcast to all web servers from here.
        """
        # Update version if we have successfully built HTML output
        try:
            if html:
                version = api_v2.version(self.version.pk)
                version.patch({
                    'built': True,
                })
        except HttpClientError:
            log.exception(
                'Updating version failed, skipping file sync: version=%s',
                self.version,
            )
        hostname = socket.gethostname()

        delete_unsynced_media = True

        if getattr(storage, 'write_build_media', False):
            # Handle the case where we want to upload some built assets to our storage
            move_files.delay(
                self.version.pk,
                hostname,
                self.config.doctype,
                html=False,
                search=False,
                localmedia=localmedia,
                pdf=pdf,
                epub=epub,
                delete_unsynced_media=delete_unsynced_media,
            )
            # Set variables so they don't get synced in the next broadcast step
            localmedia = False
            pdf = False
            epub = False
            delete_unsynced_media = False

        # Broadcast finalization steps to web application instances
        broadcast(
            type='app',
            task=sync_files,
            args=[
                self.project.pk,
                self.version.pk,
                self.config.doctype,
            ],
            kwargs=dict(
                hostname=hostname,
                html=html,
                localmedia=localmedia,
                search=search,
                pdf=pdf,
                epub=epub,
                delete_unsynced_media=delete_unsynced_media,
            ),
            callback=sync_callback.s(
                version_pk=self.version.pk,
                commit=self.build['commit'],
            ),
        )

    def setup_python_environment(self):
        """
        Build the virtualenv and install the project into it.

        Always build projects with a virtualenv.

        :param build_env: Build environment to pass commands and execution through.
        """
        self.build_env.update_build(state=BUILD_STATE_INSTALLING)

        with self.project.repo_nonblockinglock(version=self.version):
            # Check if the python version/build image in the current venv is the
            # same to be used in this build and if it differs, wipe the venv to
            # avoid conflicts.
            if self.python_env.is_obsolete:
                self.python_env.delete_existing_venv_dir()
            else:
                self.python_env.delete_existing_build_dir()

            self.python_env.setup_base()
            self.python_env.save_environment_json()
            self.python_env.install_core_requirements()
            self.python_env.install_requirements()

    def build_docs(self):
        """
        Wrapper to all build functions.

        Executes the necessary builds for this task and returns whether the
        build was successful or not.

        :returns: Build outcomes with keys for html, search, localmedia, pdf,
                  and epub
        :rtype: dict
        """
        self.build_env.update_build(state=BUILD_STATE_BUILDING)
        before_build.send(sender=self.version)

        outcomes = defaultdict(lambda: False)
        with self.project.repo_nonblockinglock(version=self.version):
            outcomes['html'] = self.build_docs_html()
            outcomes['search'] = self.build_docs_search()
            outcomes['localmedia'] = self.build_docs_localmedia()
            outcomes['pdf'] = self.build_docs_pdf()
            outcomes['epub'] = self.build_docs_epub()

        after_build.send(sender=self.version)
        return outcomes

    def build_docs_html(self):
        """Build HTML docs."""
        html_builder = get_builder_class(self.config.doctype)(
            build_env=self.build_env,
            python_env=self.python_env,
        )
        if self.build_force:
            html_builder.force()
        html_builder.append_conf()
        success = html_builder.build()
        if success:
            html_builder.move()

        # Gracefully attempt to move files via task on web workers.
        try:
            broadcast(
                type='app',
                task=move_files,
                args=[
                    self.version.pk,
                    socket.gethostname(), self.config.doctype
                ],
                kwargs=dict(html=True),
            )
        except socket.error:
            log.exception('move_files task has failed on socket error.')

        return success

    def build_docs_search(self):
        """Build search data."""
        # Search is always run in sphinx using the rtd-sphinx-extension.
        # Mkdocs has no search currently.
        if self.is_type_sphinx():
            return True
        return False

    def build_docs_localmedia(self):
        """Get local media files with separate build."""
        if 'htmlzip' not in self.config.formats:
            return False
        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_singlehtmllocalmedia')
        return False

    def build_docs_pdf(self):
        """Build PDF docs."""
        if 'pdf' not in self.config.formats:
            return False
        # Mkdocs has no pdf generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class('sphinx_pdf')
        return False

    def build_docs_epub(self):
        """Build ePub docs."""
        if 'epub' not in self.config.formats:
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

    def send_notifications(self):
        """Send notifications on build failure."""
        send_notifications.delay(self.version.pk, build_pk=self.build['id'])

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return 'sphinx' in self.config.doctype


# Web tasks
@app.task(queue='web')
def sync_files(
        project_pk, version_pk, doctype, hostname=None, html=False,
        localmedia=False, search=False, pdf=False, epub=False,
        delete_unsynced_media=False,
):
    """
    Sync build artifacts to application instances.

    This task broadcasts from a build instance on build completion and performs
    synchronization of build artifacts on each application instance.
    """
    # Clean up unused artifacts
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return

    # Sync files to the web servers
    move_files(
        version_pk,
        hostname,
        doctype,
        html=html,
        localmedia=localmedia,
        search=search,
        pdf=pdf,
        epub=epub,
        delete_unsynced_media=delete_unsynced_media,
    )

    # Symlink project
    symlink_project(project_pk)

    # Update metadata
    update_static_metadata(project_pk)


@app.task(queue='web')
def move_files(
        version_pk,
        hostname,
        doctype,
        html=False,
        localmedia=False,
        search=False,
        pdf=False,
        epub=False,
        delete_unsynced_media=False,
):
    """
    Task to move built documentation to web servers.

    :param version_pk: Version id to sync files for
    :param hostname: Hostname to sync to
    :param html: Sync HTML
    :type html: bool
    :param localmedia: Sync local media files
    :type localmedia: bool
    :param search: Sync search files
    :type search: bool
    :param pdf: Sync PDF files
    :type pdf: bool
    :param epub: Sync ePub files
    :type epub: bool
    :param delete_unsynced_media: Whether to try and delete files.
    :type delete_unsynced_media: bool
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return

    # This is False if we have already synced media files to blob storage
    # We set `epub=False` for example so data doesn't get re-uploaded on each
    # web, so we need this to protect against deleting in those cases
    if delete_unsynced_media:
        downloads = {
            'pdf': pdf,
            'epub': epub,
            'htmlzip': localmedia,
        }
        unsync_downloads = (k for k, v in downloads.items() if not v)
        for media_type in unsync_downloads:
            remove_dirs([
                version.project.get_production_media_path(
                    type_=media_type,
                    version_slug=version.slug,
                    include_file=False,
                ),
            ])

            if getattr(storage, 'write_build_media', False):
                # Remove the media from remote storage if it exists
                storage_path = version.project.get_storage_path(
                    type_=media_type,
                    version_slug=version.slug,
                )
                if storage.exists(storage_path):
                    log.info('Removing %s from media storage', storage_path)
                    storage.delete(storage_path)

    log.debug(
        LOG_TEMPLATE.format(
            project=version.project.slug,
            version=version.slug,
            msg='Moving files',
        ),
    )

    if html:
        from_path = version.project.artifact_path(
            version=version.slug,
            type_=doctype,
        )
        target = version.project.rtd_build_path(version.slug)
        Syncer.copy(from_path, target, host=hostname)

    if search:
        from_path = version.project.artifact_path(
            version=version.slug,
            type_='sphinx_search',
        )
        to_path = version.project.get_production_media_path(
            type_='json',
            version_slug=version.slug,
            include_file=False,
        )
        Syncer.copy(from_path, to_path, host=hostname)

    if localmedia:
        from_path = os.path.join(
            version.project.artifact_path(
                version=version.slug,
                type_='sphinx_localmedia',
            ),
            '{}.zip'.format(version.project.slug),
        )
        to_path = version.project.get_production_media_path(
            type_='htmlzip',
            version_slug=version.slug,
            include_file=True,
        )
        Syncer.copy(from_path, to_path, host=hostname, is_file=True)
    if pdf:
        from_path = os.path.join(
            version.project.artifact_path(
                version=version.slug,
                type_='sphinx_pdf',
            ),
            '{}.pdf'.format(version.project.slug),
        )
        to_path = version.project.get_production_media_path(
            type_='pdf',
            version_slug=version.slug,
            include_file=True,
        )
        Syncer.copy(from_path, to_path, host=hostname, is_file=True)
    if epub:
        from_path = os.path.join(
            version.project.artifact_path(
                version=version.slug,
                type_='sphinx_epub',
            ),
            '{}.epub'.format(version.project.slug),
        )
        to_path = version.project.get_production_media_path(
            type_='epub',
            version_slug=version.slug,
            include_file=True,
        )
        Syncer.copy(from_path, to_path, host=hostname, is_file=True)


@app.task(queue='web')
def symlink_project(project_pk):
    project = Project.objects.get(pk=project_pk)
    for symlink in [PublicSymlink, PrivateSymlink]:
        sym = symlink(project=project)
        sym.run()


@app.task(queue='web')
def symlink_domain(project_pk, domain, delete=False):
    """
    Symlink domain.

    :param project_pk: project's pk
    :type project_pk: int
    :param domain: domain for the symlink
    :type domain: str
    """
    project = Project.objects.get(pk=project_pk)
    for symlink in [PublicSymlink, PrivateSymlink]:
        sym = symlink(project=project)
        if delete:
            sym.remove_symlink_cname(domain)
        else:
            sym.symlink_cnames(domain)


@app.task(queue='web')
def remove_orphan_symlinks():
    """
    Remove orphan symlinks.

    List CNAME_ROOT for Public and Private symlinks, check that all the listed
    cname exist in the database and if doesn't exist, they are un-linked.
    """
    for symlink in [PublicSymlink, PrivateSymlink]:
        for domain_path in [symlink.PROJECT_CNAME_ROOT, symlink.CNAME_ROOT]:
            valid_cnames = set(
                Domain.objects.all().values_list('domain', flat=True),
            )
            orphan_cnames = set(os.listdir(domain_path)) - valid_cnames
            for cname in orphan_cnames:
                orphan_domain_path = os.path.join(domain_path, cname)
                log.info('Unlinking orphan CNAME: %s', orphan_domain_path)
                safe_unlink(orphan_domain_path)


@app.task(queue='web')
def broadcast_remove_orphan_symlinks():
    """
    Broadcast the task ``remove_orphan_symlinks`` to all our web servers.

    This task is executed by CELERY BEAT.
    """
    broadcast(type='web', task=remove_orphan_symlinks, args=[])


@app.task(queue='web')
def symlink_subproject(project_pk):
    project = Project.objects.get(pk=project_pk)
    for symlink in [PublicSymlink, PrivateSymlink]:
        sym = symlink(project=project)
        sym.symlink_subprojects()


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return
    project = version.project

    if not commit:
        log.warning(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg=(
                    'Search index not being built because no commit information'
                ),
            ),
        )
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(
            LOG_TEMPLATE.format(
                project=version.project.slug,
                version=version.slug,
                msg='Creating ImportedFiles',
            ),
        )
        try:
            _manage_imported_files(version, path, commit)
        except Exception:
            log.exception('Failed during ImportedFile creation')

        try:
            _update_intersphinx_data(version, path, commit)
        except Exception:
            log.exception('Failed during SphinxDomain creation')


def _update_intersphinx_data(version, path, commit):
    """
    Update intersphinx data for this version

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    object_file = os.path.join(path, 'objects.inv')
    if not os.path.exists(object_file):
        log.debug('No objects.inv, skipping intersphinx indexing.')
        return

    full_json_path = version.project.get_production_media_path(
        type_='json', version_slug=version.slug, include_file=False
    )
    type_file = os.path.join(full_json_path, 'readthedocs-sphinx-domain-names.json')
    types = {}
    titles = {}
    if os.path.exists(type_file):
        try:
            data = json.load(open(type_file))
            types = data['types']
            titles = data['titles']
        except Exception:
            log.exception('Exception parsing readthedocs-sphinx-domain-names.json')

    # These classes are copied from Sphinx
    # https://git.io/fhFbI
    class MockConfig:
        intersphinx_timeout = None
        tls_verify = False

    class MockApp:
        srcdir = ''
        config = MockConfig()

        def warn(self, msg):
            log.warning('Sphinx MockApp: %s', msg)

    created_sphinx_domains = []

    invdata = intersphinx.fetch_inventory(MockApp(), '', object_file)
    for key, value in sorted(invdata.items() or {}):
        domain, _type = key.split(':')
        for name, einfo in sorted(value.items()):
            # project, version, url, display_name
            # ('Sphinx', '1.7.9', 'faq.html#epub-faq', 'Epub info')
            url = einfo[2]
            if '#' in url:
                doc_name, anchor = url.split(
                    '#',
                    # The anchor can contain ``#`` characters
                    maxsplit=1
                )
            else:
                doc_name, anchor = url, ''
            display_name = einfo[3]
            obj, created = SphinxDomain.objects.get_or_create(
                project=version.project,
                version=version,
                domain=domain,
                name=name,
                display_name=display_name,
                type=_type,
                type_display=types.get(f'{domain}:{_type}', ''),
                doc_name=doc_name,
                doc_display=titles.get(doc_name, ''),
                anchor=anchor,
            )
            if obj.commit != commit:
                obj.commit = commit
                obj.save()
            if created:
                created_sphinx_domains.append(obj)

    # Send bulk_post_create signal for bulk indexing to Elasticsearch
    bulk_post_create.send(sender=SphinxDomain, instance_list=created_sphinx_domains, commit=commit)

    # Delete the SphinxDomain first from previous commit and
    # send bulk_post_delete signal for bulk removing from Elasticsearch
    delete_queryset = (
        SphinxDomain.objects.filter(project=version.project,
                                    version=version
                                    ).exclude(commit=commit)
    )
    # Keep the objects into memory to send it to signal
    instance_list = list(delete_queryset)
    # Always pass the list of instance, not queryset.
    bulk_post_delete.send(sender=SphinxDomain, instance_list=instance_list, commit=commit)

    # Delete from previous versions
    delete_queryset.delete()


def _manage_imported_files(version, path, commit):
    """
    Update imported files for version.

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    changed_files = set()
    created_html_files = []
    for root, __, filenames in os.walk(path):
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.html'):
                model_class = HTMLFile
            else:
                model_class = ImportedFile

            dirpath = os.path.join(
                root.replace(path, '').lstrip('/'), filename.lstrip('/')
            )
            full_path = os.path.join(root, filename)
            md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            try:
                # pylint: disable=unpacking-non-sequence
                obj, created = model_class.objects.get_or_create(
                    project=version.project,
                    version=version,
                    path=dirpath,
                    name=filename,
                )
            except model_class.MultipleObjectsReturned:
                log.warning('Error creating ImportedFile')
                continue
            if obj.md5 != md5:
                obj.md5 = md5
                changed_files.add(dirpath)
            if obj.commit != commit:
                obj.commit = commit
            obj.save()

            if created and model_class == HTMLFile:
                # the `obj` is HTMLFile, so add it to the list
                created_html_files.append(obj)

    # Send bulk_post_create signal for bulk indexing to Elasticsearch
    bulk_post_create.send(sender=HTMLFile, instance_list=created_html_files,
                          version=version, commit=commit)

    # Delete the HTMLFile first from previous commit and
    # send bulk_post_delete signal for bulk removing from Elasticsearch
    delete_queryset = (
        HTMLFile.objects.filter(project=version.project,
                                version=version).exclude(commit=commit)
    )

    # Keep the objects into memory to send it to signal
    instance_list = list(delete_queryset)

    # Always pass the list of instance, not queryset.
    # These objects must exist though,
    # because the task will query the DB for the objects before deleting
    bulk_post_delete.send(sender=HTMLFile, instance_list=instance_list,
                          version=version, commit=commit)

    # Delete ImportedFiles from previous versions
    delete_queryset.delete()

    # This is required to delete ImportedFile objects that aren't HTMLFile objects,
    ImportedFile.objects.filter(
        project=version.project, version=version
    ).exclude(commit=commit).delete()

    changed_files = [
        resolve_path(
            version.project,
            filename=file,
            version_slug=version.slug,
        ) for file in changed_files
    ]
    files_changed.send(
        sender=Project,
        project=version.project,
        files=changed_files,
    )


@app.task(queue='web')
def send_notifications(version_pk, build_pk):
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return
    build = Build.objects.get(pk=build_pk)

    for hook in version.project.webhook_notifications.all():
        webhook_notification(version, build, hook.url)
    for email in version.project.emailhook_notifications.all().values_list(
            'email',
            flat=True,
    ):
        email_notification(version, build, email)


def email_notification(version, build, email):
    """
    Send email notifications for build failure.

    :param version: :py:class:`Version` instance that failed
    :param build: :py:class:`Build` instance that failed
    :param email: Email recipient address
    """
    log.debug(
        LOG_TEMPLATE.format(
            project=version.project.slug,
            version=version.slug,
            msg='sending email to: %s' % email,
        ),
    )

    # We send only what we need from the Django model objects here to avoid
    # serialization problems in the ``readthedocs.core.tasks.send_email_task``
    context = {
        'version': {
            'verbose_name': version.verbose_name,
        },
        'project': {
            'name': version.project.name,
        },
        'build': {
            'pk': build.pk,
            'error': build.error,
        },
        'build_url': 'https://{}{}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            build.get_absolute_url(),
        ),
        'unsub_url': 'https://{}{}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            reverse('projects_notifications', args=[version.project.slug]),
        ),
    }

    if build.commit:
        title = _(
            'Failed: {project[name]} ({commit})',
        ).format(commit=build.commit[:8], **context)
    else:
        title = _('Failed: {project[name]} ({version[verbose_name]})').format(
            **context
        )

    send_email(
        email,
        title,
        template='projects/email/build_failed.txt',
        template_html='projects/email/build_failed.html',
        context=context,
    )


def webhook_notification(version, build, hook_url):
    """
    Send webhook notification for project webhook.

    :param version: Version instance to send hook for
    :param build: Build instance that failed
    :param hook_url: Hook URL to send to
    """
    project = version.project

    data = json.dumps({
        'name': project.name,
        'slug': project.slug,
        'build': {
            'id': build.id,
            'success': build.success,
            'date': build.date.strftime('%Y-%m-%d %H:%M:%S'),
        },
    })
    log.debug(
        LOG_TEMPLATE.format(
            project=project.slug,
            version='',
            msg='sending notification to: %s' % hook_url,
        ),
    )
    try:
        requests.post(hook_url, data=data)
    except Exception:
        log.exception('Failed to POST on webhook url: url=%s', hook_url)


@app.task(queue='web')
def update_static_metadata(project_pk, path=None):
    """
    Update static metadata JSON file.

    Metadata settings include the following project settings:

    version
      The default version for the project, default: `latest`

    language
      The default language for the project, default: `en`

    languages
      List of languages built by linked translation projects.
    """
    project = Project.objects.get(pk=project_pk)
    if not path:
        path = project.static_metadata_path()

    log.info(
        LOG_TEMPLATE.format(
            project=project.slug,
            version='',
            msg='Updating static metadata',
        ),
    )
    translations = [trans.language for trans in project.translations.all()]
    languages = set(translations)
    # Convert to JSON safe types
    metadata = {
        'version': project.default_version,
        'language': project.language,
        'languages': list(languages),
        'single_version': project.single_version,
        'subdomain': project.subdomain(),
        'canonical_url': project.get_canonical_url(),
    }
    try:
        fh = open(path, 'w+')
        json.dump(metadata, fh)
        fh.close()
    except (AttributeError, IOError) as e:
        log.debug(
            LOG_TEMPLATE.format(
                project=project.slug,
                version='',
                msg='Cannot write to metadata.json: {}'.format(e),
            ),
        )


# Random Tasks
@app.task()
def remove_dirs(paths):
    """
    Remove artifacts from servers.

    This is mainly a wrapper around shutil.rmtree so that we can remove things across
    every instance of a type of server (eg. all builds or all webs).

    :param paths: list containing PATHs where file is on disk
    """
    for path in paths:
        log.info('Removing %s', path)
        shutil.rmtree(path, ignore_errors=True)


@app.task(queue='web')
def sync_callback(_, version_pk, commit, *args, **kwargs):
    """
    Called once the sync_files tasks are done.

    The first argument is the result from previous tasks, which we discard.
    """
    try:
        fileify(version_pk, commit=commit)
    except Exception:
        log.exception('Post sync tasks failed, not stopping build')


@app.task()
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if it's not in ``FINISHED`` state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``FINISHED`` with an
    ``error`` to be communicated to the user.
    """
    time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    delta = datetime.timedelta(seconds=time_limit)
    query = (
        ~Q(state=BUILD_STATE_FINISHED) & Q(date__lte=timezone.now() - delta)
    )

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as FINISHED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({}).'.format(build.pk),
        )
        build.save()
        builds_finished += 1

    log.info(
        'Builds marked as "Terminated due inactivity": %s',
        builds_finished,
    )


@app.task(queue='web')
def retry_domain_verification(domain_pk):
    """
    Trigger domain verification on a domain.

    :param domain_pk: a `Domain` pk to verify
    """
    domain = Domain.objects.get(pk=domain_pk)
    domain_verify.send(
        sender=domain.__class__,
        domain=domain,
    )
