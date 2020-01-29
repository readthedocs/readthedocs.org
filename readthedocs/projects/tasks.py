"""
Tasks related to projects.

This includes fetching repository code, cleaning ``conf.py`` files, and
rebuilding documentation.
"""

import datetime
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

from readthedocs.api.v2.client import api as api_v2
from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_INSTALLING,
    BUILD_STATUS_SUCCESS,
    BUILD_STATUS_FAILURE,
    LATEST,
    LATEST_VERBOSE_NAME,
    STABLE_VERBOSE_NAME,
    EXTERNAL,
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
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.notifications import GitBuildStatusFailureNotification
from readthedocs.projects.constants import GITHUB_BRAND, GITLAB_BRAND
from readthedocs.projects.models import APIProject, Feature
from readthedocs.search.utils import index_new_files, remove_indexed_files
from readthedocs.sphinx_domains.models import SphinxDomain
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
    domain_verify,
    files_changed,
)


log = logging.getLogger(__name__)


class SyncRepositoryMixin:

    """Mixin that handles the VCS sync/update."""

    @staticmethod
    def get_version(version_pk):
        """
        Retrieve version data from the API.

        :param version_pk: version pk to sync
        :type version_pk: int
        :returns: a data-complete version object
        :rtype: builds.models.APIVersion
        """
        version_data = api_v2.version(version_pk).get()
        return APIVersion(**version_data)

    def get_vcs_repo(self, environment):
        """
        Get the VCS object of the current project.

        All VCS commands will be executed using `environment`.
        """
        version_repo = self.project.vcs_repo(
            version=self.version.slug,
            environment=environment,
            verbose_name=self.version.verbose_name,
            version_type=self.version.type
        )
        return version_repo

    def sync_repo(self, environment):
        """Update the project's repository and hit ``sync_versions`` API."""
        # Make Dirs
        if not os.path.exists(self.project.doc_path):
            os.makedirs(self.project.doc_path)

        if not self.project.vcs_class():
            raise RepositoryError(
                _('Repository type "{repo_type}" unknown').format(
                    repo_type=self.project.repo_type,
                ),
            )

        # Get the actual code on disk
        msg = 'Checking out version {slug}: {identifier}'.format(
            slug=self.version.slug,
            identifier=self.version.identifier,
        )
        log.info(
            LOG_TEMPLATE,
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'msg': msg,
            }
        )
        version_repo = self.get_vcs_repo(environment)
        version_repo.update()
        self.sync_versions(version_repo)
        identifier = getattr(self, 'commit', None) or self.version.identifier
        version_repo.checkout(identifier)

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

    def get_rtd_env_vars(self):
        """Get bash environment variables specific to Read the Docs."""
        env = {
            'READTHEDOCS': 'True',
            'READTHEDOCS_VERSION': self.version.slug,
            'READTHEDOCS_PROJECT': self.project.slug,
            'READTHEDOCS_LANGUAGE': self.project.language,
        }
        return env


@app.task(max_retries=5, default_retry_delay=7 * 60)
def sync_repository_task(version_pk):
    """Celery task to trigger VCS version sync."""
    try:
        step = SyncRepositoryTaskStep()
        return step.run(version_pk)
    finally:
        clean_build(version_pk)


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
            self.version = self.get_version(version_pk)
            self.project = self.version.project

            if settings.DOCKER_ENABLE:
                env_cls = DockerBuildEnvironment
            else:
                env_cls = LocalBuildEnvironment
            environment = env_cls(
                project=self.project,
                version=self.version,
                record=False,
                update_on_success=False,
                environment=self.get_rtd_env_vars(),
            )

            with environment:
                before_vcs.send(sender=self.version, environment=environment)
                with self.project.repo_nonblockinglock(version=self.version):
                    self.sync_repo(environment)
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
        finally:
            after_vcs.send(sender=self.version)

        # Always return False for any exceptions
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
def update_docs_task(self, version_pk, *args, **kwargs):
    try:
        step = UpdateDocsTaskStep(task=self)
        return step.run(version_pk, *args, **kwargs)
    finally:
        clean_build(version_pk)


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
            commit=None,
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
        self.commit = commit
        self.project = {}
        if project is not None:
            self.project = project
        if config is not None:
            self.config = config
        self.task = task
        # TODO: remove this
        self.setup_env = None

    # pylint: disable=arguments-differ
    def run(
            self, version_pk, build_pk=None, commit=None, record=True,
            force=False, **__
    ):
        """
        Run a documentation sync n' build.

        This is fully wrapped in exception handling to account for a number of
        failure cases. We first run a few commands in a build environment,
        but do not report on environment success. This avoids a flicker on the
        build output page where the build is marked as finished in between the
        checkout steps and the build steps.

        If a failure is raised, or the build is not successful, return
        ``False``, otherwise, ``True``.

        Unhandled exceptions raise a generic user facing error, which directs
        the user to bug us. It is therefore a benefit to have as few unhandled
        errors as possible.

        :param version_pk int: Project Version id
        :param build_pk int: Build id (if None, commands are not recorded)
        :param commit: commit sha of the version required for sending build status reports
        :param record bool: record a build object in the database
        :param force bool: force Sphinx build

        :returns: whether build was successful or not

        :rtype: bool
        """
        try:
            self.version = self.get_version(version_pk)
            self.project = self.version.project
            self.build = self.get_build(build_pk)
            self.build_force = force
            self.commit = commit
            self.config = None

            # Build process starts here
            setup_successful = self.run_setup(record=record)
            if not setup_successful:
                return False
            self.run_build(record=record)
            return True
        except Exception:
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
            # We should check first for build_env.
            # If isn't None, it means that something got wrong
            # in the second step (`self.run_build`)
            if self.build_env is not None:
                self.build_env.failure = BuildEnvironmentError(
                    BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                        build_id=build_pk,
                    ),
                )
                self.build_env.update_build(BUILD_STATE_FINISHED)
            elif self.setup_env is not None:
                self.setup_env.failure = BuildEnvironmentError(
                    BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                        build_id=build_pk,
                    ),
                )
                self.setup_env.update_build(BUILD_STATE_FINISHED)

            # Send notifications for unhandled errors
            self.send_notifications(version_pk, build_pk, email=True)
            return False

    def run_setup(self, record=True):
        """
        Run setup in a build environment.

        Return True if successful.
        """
        if settings.DOCKER_ENABLE:
            env_cls = DockerBuildEnvironment
        else:
            env_cls = LocalBuildEnvironment

        environment = env_cls(
            project=self.project,
            version=self.version,
            build=self.build,
            record=record,
            update_on_success=False,
            environment=self.get_rtd_env_vars(),
        )

        # TODO: Remove.
        # There is code that still depends of this attribute
        # outside this function. Don't use self.setup_env for new code.
        self.setup_env = environment

        # Environment used for code checkout & initial configuration reading
        with environment:
            try:
                before_vcs.send(sender=self.version, environment=environment)
                if self.project.skip:
                    raise ProjectBuildsSkippedError
                try:
                    with self.project.repo_nonblockinglock(version=self.version):
                        self.setup_vcs(environment)
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
                self.additional_vcs_operations(environment)
            finally:
                after_vcs.send(sender=self.version)

        if environment.failure or self.config is None:
            msg = 'Failing build because of setup failure: {}'.format(
                environment.failure,
            )
            log.info(
                LOG_TEMPLATE,
                {
                    'project': self.project.slug,
                    'version': self.version.slug,
                    'msg': msg,
                }
            )

            # Send notification to users only if the build didn't fail because
            # of VersionLockedError: this exception occurs when a build is
            # triggered before the previous one has finished (e.g. two webhooks,
            # one after the other)
            if not isinstance(environment.failure, VersionLockedError):
                self.send_notifications(self.version.pk, self.build['id'], email=True)

            return False

        if environment.successful and not self.project.has_valid_clone:
            self.set_valid_clone()

        return True

    def additional_vcs_operations(self, environment):
        """
        Execution of tasks that involve the project's VCS.

        All this tasks have access to the configuration object.
        """
        version_repo = self.get_vcs_repo(environment)
        if version_repo.supports_submodules:
            version_repo.update_submodules(self.config)

    def run_build(self, record):
        """
        Build the docs in an environment.

        :param record: whether or not record all the commands in the ``Build``
            instance
        """
        env_vars = self.get_env_vars()

        if settings.DOCKER_ENABLE:
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
                    LOG_TEMPLATE,
                    {
                        'project': self.project.slug,
                        'version': self.version.slug,
                        'msg': 'Using conda',
                    }
                )
                python_env_cls = Conda
            self.python_env = python_env_cls(
                version=self.version,
                build_env=self.build_env,
                config=self.config,
            )

            try:
                before_build.send(
                    sender=self.version,
                    environment=self.build_env,
                )
                with self.project.repo_nonblockinglock(version=self.version):
                    self.setup_python_environment()

                    # TODO the build object should have an idea of these states,
                    # extend the model to include an idea of these outcomes
                    outcomes = self.build_docs()
            except vcs_support_utils.LockTimeout as e:
                self.task.retry(exc=e, throw=False)
                raise VersionLockedError
            except SoftTimeLimitExceeded:
                raise BuildTimeoutError
            else:
                build_id = self.build.get('id')
                if build_id:
                    # Store build artifacts to storage (local or cloud storage)
                    self.store_build_artifacts(
                        html=bool(outcomes['html']),
                        search=bool(outcomes['search']),
                        localmedia=bool(outcomes['localmedia']),
                        pdf=bool(outcomes['pdf']),
                        epub=bool(outcomes['epub']),
                    )

                    # Finalize build and update web servers
                    # We upload EXTERNAL version media files to blob storage
                    # We should have this check here to make sure
                    # the files don't get re-uploaded on web.
                    if self.version.type != EXTERNAL:
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
            # Send Webhook and email notification for build failure.
            self.send_notifications(self.version.pk, self.build['id'], email=True)

            if self.commit:
                send_external_build_status(
                    version_type=self.version.type,
                    build_pk=self.build['id'],
                    commit=self.commit,
                    status=BUILD_STATUS_FAILURE
                )
        elif self.build_env.successful:
            # Send Webhook notification for build success.
            self.send_notifications(self.version.pk, self.build['id'], email=False)

            if self.commit:
                send_external_build_status(
                    version_type=self.version.type,
                    build_pk=self.build['id'],
                    commit=self.commit,
                    status=BUILD_STATUS_SUCCESS
                )
        else:
            if self.commit:
                msg = 'Unhandled Build Status'
                send_external_build_status(
                    version_type=self.version.type,
                    build_pk=self.build['id'],
                    commit=self.commit,
                    status=BUILD_STATUS_FAILURE
                )
                log.warning(
                    LOG_TEMPLATE,
                    {
                        'project': self.project.slug,
                        'version': self.version.slug,
                        'msg': msg,
                    }
                )

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

    def setup_vcs(self, environment):
        """
        Update the checkout of the repo to make sure it's the latest.

        This also syncs versions in the DB.
        """
        environment.update_build(state=BUILD_STATE_CLONING)

        log.info(
            LOG_TEMPLATE,
            {
                'project': self.project.slug,
                'version': self.version.slug,
                'msg': 'Updating docs from VCS',
            }
        )
        try:
            self.sync_repo(environment)
        except RepositoryError:
            log.warning('There was an error with the repository', exc_info=True)
            # Re raise the exception to stop the build at this point
            raise
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

        commit = self.commit or self.project.vcs_repo(self.version.slug).commit
        if commit:
            self.build['commit'] = commit

    def get_env_vars(self):
        """Get bash environment variables used for all builder commands."""
        env = self.get_rtd_env_vars()

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
        # avoiding to expose environment variables if the version is external
        # for security reasons.
        if self.version.type != EXTERNAL:
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

        This looks very similar to `move_files` and is intended to replace it!

        :param html: whether to save HTML output
        :param localmedia: whether to save localmedia (htmlzip) output
        :param search: whether to save search artifacts
        :param pdf: whether to save PDF output
        :param epub: whether to save ePub output
        """
        if not settings.RTD_BUILD_MEDIA_STORAGE:
            # Note: this check can be removed once corporate build servers use storage
            log.warning(
                LOG_TEMPLATE,
                {
                    'project': self.version.project.slug,
                    'version': self.version.slug,
                    'msg': (
                        'RTD_BUILD_MEDIA_STORAGE is missing - '
                        'Not writing build artifacts to media storage'
                    ),
                },
            )
            return

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        log.info(
            LOG_TEMPLATE,
            {
                'project': self.version.project.slug,
                'version': self.version.slug,
                'msg': 'Writing build artifacts to media storage',
            },
        )

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
            log.info(
                LOG_TEMPLATE,
                {
                    'project': self.version.project.slug,
                    'version': self.version.slug,
                    'msg': f'Writing {media_type} to media storage - {to_path}',
                },
            )
            try:
                storage.sync_directory(from_path, to_path)
            except Exception:
                # Ideally this should just be an IOError
                # but some storage backends unfortunately throw other errors
                log.exception(
                    LOG_TEMPLATE,
                    {
                        'project': self.version.project.slug,
                        'version': self.version.slug,
                        'msg': f'Error copying {from_path} to storage (not failing build)',
                    },
                )

        for media_type in types_to_delete:
            media_path = self.version.project.get_storage_path(
                type_=media_type,
                version_slug=self.version.slug,
                include_file=False,
                version_type=self.version.type,
            )
            log.info(
                LOG_TEMPLATE,
                {
                    'project': self.version.project.slug,
                    'version': self.version.slug,
                    'msg': f'Deleting {media_type} from media storage - {media_path}',
                },
            )
            try:
                storage.delete_directory(media_path)
            except Exception:
                # Ideally this should just be an IOError
                # but some storage backends unfortunately throw other errors
                log.exception(
                    LOG_TEMPLATE,
                    {
                        'project': self.version.project.slug,
                        'version': self.version.slug,
                        'msg': f'Error deleting {media_path} from storage (not failing build)',
                    },
                )

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
        # And store whether the build had other media types
        try:
            if html:
                version = api_v2.version(self.version.pk)
                version.patch({
                    'built': True,
                    'documentation_type': self.config.doctype,
                    'has_pdf': pdf,
                    'has_epub': epub,
                    'has_htmlzip': localmedia,
                })
        except HttpClientError:
            log.exception(
                'Updating version failed, skipping file sync: version=%s',
                self.version,
            )
        hostname = socket.gethostname()

        delete_unsynced_media = True

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
                build=self.build['id'],
            ),
        )

    def setup_python_environment(self):
        """
        Build the virtualenv and install the project into it.

        Always build projects with a virtualenv.

        :param build_env: Build environment to pass commands and execution through.
        """
        self.build_env.update_build(state=BUILD_STATE_INSTALLING)

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

        outcomes = defaultdict(lambda: False)
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
            # We upload EXTERNAL version media files to blob storage
            # We should have this check here to make sure
            # the files don't get re-uploaded on web.
            if self.version.type != EXTERNAL:
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
        if self.is_type_sphinx() and self.version.type != EXTERNAL:
            return True
        return False

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

    def send_notifications(self, version_pk, build_pk, email=False):
        """Send notifications on build failure."""
        # Try to infer the version type if we can
        # before creating a task.
        if not self.version or self.version.type != EXTERNAL:
            send_notifications.delay(version_pk, build_pk=build_pk, email=email)

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return 'sphinx' in self.config.doctype


# Web tasks
@app.task(queue='web')
def sync_files(
        project_pk,
        version_pk,
        doctype,
        hostname=None,
        html=False,
        localmedia=False,
        search=False,
        pdf=False,
        epub=False,
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

    log.debug(
        LOG_TEMPLATE,
        {
            'project': version.project.slug,
            'version': version.slug,
            'msg': 'Moving files',
        }
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
def fileify(version_pk, commit, build):
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
            LOG_TEMPLATE,
            {
                'project': project.slug,
                'version': version.slug,
                'msg': (
                    'Search index not being built because no commit information'
                ),
            },
        )
        return

    log.info(
        LOG_TEMPLATE,
        {
            'project': version.project.slug,
            'version': version.slug,
            'msg': 'Creating ImportedFiles',
        }
    )
    try:
        changed_files = _create_imported_files(version, commit, build)
    except Exception:
        changed_files = set()
        log.exception('Failed during ImportedFile creation')

    try:
        _create_intersphinx_data(version, commit, build)
    except Exception:
        log.exception('Failed during SphinxDomain creation')

    try:
        _sync_imported_files(version, build, changed_files)
    except Exception:
        log.exception('Failed during ImportedFile syncing')


def _create_intersphinx_data(version, commit, build):
    """
    Create intersphinx data for this version.

    :param version: Version instance
    :param commit: Commit that updated path
    :param build: Build id
    """
    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    html_storage_path = version.project.get_storage_path(
        type_='html', version_slug=version.slug, include_file=False
    )
    json_storage_path = version.project.get_storage_path(
        type_='json', version_slug=version.slug, include_file=False
    )

    object_file = storage.join(html_storage_path, 'objects.inv')
    if not storage.exists(object_file):
        log.debug('No objects.inv, skipping intersphinx indexing.')
        return

    type_file = storage.join(json_storage_path, 'readthedocs-sphinx-domain-names.json')
    types = {}
    titles = {}
    if storage.exists(type_file):
        try:
            data = json.load(storage.open(type_file))
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

    # Re-create all objects from the new build of the version
    object_file_url = storage.url(object_file)
    if object_file_url.startswith('/'):
        # Filesystem backed storage simply prepends MEDIA_URL to the path to get the URL
        # This can cause an issue if MEDIA_URL is not fully qualified
        object_file_url = 'http://' + settings.PRODUCTION_DOMAIN + object_file_url

    invdata = intersphinx.fetch_inventory(MockApp(), '', object_file_url)
    for key, value in sorted(invdata.items() or {}):
        domain, _type = key.split(':')
        for name, einfo in sorted(value.items()):
            # project, version, url, display_name
            # ('Sphinx', '1.7.9', 'faq.html#epub-faq', 'Epub info')
            try:
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
            except Exception:
                log.exception(
                    'Error while getting sphinx domain information for %s:%s:%s. Skipping.',
                    version.project.slug,
                    version.slug,
                    f'domain->name',
                )
                continue

            # HACK: This is done because the difference between
            # ``sphinx.builders.html.StandaloneHTMLBuilder``
            # and ``sphinx.builders.dirhtml.DirectoryHTMLBuilder``.
            # They both have different ways of generating HTML Files,
            # and therefore the doc_name generated is different.
            # More info on: http://www.sphinx-doc.org/en/master/usage/builders/index.html#builders
            # Also see issue: https://github.com/readthedocs/readthedocs.org/issues/5821
            if doc_name.endswith('/'):
                doc_name += 'index.html'

            html_file = HTMLFile.objects.filter(
                project=version.project, version=version,
                path=doc_name, build=build,
            ).first()

            if not html_file:
                log.debug('[%s] [%s] [Build: %s] HTMLFile object not found. File: %s' % (
                    version.project,
                    version,
                    build,
                    doc_name,
                ))

                # Don't create Sphinx Domain objects
                # if the HTMLFile object is not found.
                continue

            SphinxDomain.objects.create(
                project=version.project,
                version=version,
                html_file=html_file,
                domain=domain,
                name=name,
                display_name=display_name,
                type=_type,
                type_display=types.get(f'{domain}:{_type}', ''),
                doc_name=doc_name,
                doc_display=titles.get(doc_name, ''),
                anchor=anchor,
                commit=commit,
                build=build,
            )


def clean_build(version_pk):
    """Clean the files used in the build of the given version."""
    try:
        version = SyncRepositoryMixin.get_version(version_pk)
    except Exception:
        log.exception('Error while fetching the version from the api')
        return False
    if (
        not settings.RTD_CLEAN_AFTER_BUILD and
        not version.project.has_feature(Feature.CLEAN_AFTER_BUILD)
    ):
        log.info(
            'Skipping build files deletetion for version: %s',
            version_pk,
        )
        return False
    # NOTE: we are skipping the deletion of the `artifacts` dir
    # because we are syncing the servers with an async task.
    del_dirs = [
        os.path.join(version.project.doc_path, dir_, version.slug)
        for dir_ in ('checkouts', 'envs', 'conda')
    ]
    del_dirs.append(
        os.path.join(version.project.doc_path, '.cache')
    )
    try:
        with version.project.repo_nonblockinglock(version):
            log.info('Removing: %s', del_dirs)
            remove_dirs(del_dirs)
    except vcs_support_utils.LockTimeout:
        log.info('Another task is running. Not removing: %s', del_dirs)
    else:
        return True


def _create_imported_files(version, commit, build):
    """
    Create imported files for version.

    :param version: Version instance
    :param commit: Commit that updated path
    :param build: Build id
    :returns: paths of changed files
    :rtype: set
    """
    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    changed_files = set()

    # Re-create all objects from the new build of the version
    storage_path = version.project.get_storage_path(
        type_='html', version_slug=version.slug, include_file=False
    )
    for root, __, filenames in storage.walk(storage_path):
        for filename in filenames:
            if filename.endswith('.html'):
                model_class = HTMLFile
            elif version.project.cdn_enabled:
                # We need to track all files for CDN enabled projects so the files can be purged
                model_class = ImportedFile
            else:
                # For projects not behind a CDN, we don't care about non-HTML
                continue

            full_path = storage.join(root, filename)

            # Generate a relative path for storage similar to os.path.relpath
            relpath = full_path.replace(storage_path, '', 1).lstrip('/')

            try:
                md5 = hashlib.md5(storage.open(full_path, 'rb').read()).hexdigest()
            except Exception:
                log.exception(
                    'Error while generating md5 for %s:%s:%s. Don\'t stop.',
                    version.project.slug,
                    version.slug,
                    relpath,
                )
                md5 = ''
            # Keep track of changed files to be purged in the CDN
            obj = (
                model_class.objects
                .filter(project=version.project, version=version, path=relpath)
                .order_by('-modified_date')
                .first()
            )
            if obj and md5 and obj.md5 != md5:
                changed_files.add(
                    resolve_path(
                        version.project,
                        filename=relpath,
                        version_slug=version.slug,
                    ),
                )
            # Create imported files from new build
            model_class.objects.create(
                project=version.project,
                version=version,
                path=relpath,
                name=filename,
                md5=md5,
                commit=commit,
                build=build,
            )

    return changed_files


def _sync_imported_files(version, build, changed_files):
    """
    Sync/Update/Delete ImportedFiles objects of this version.

    :param version: Version instance
    :param build: Build id
    :param changed_files: path of changed files
    """

    # Index new HTMLFiles to ElasticSearch
    index_new_files(model=HTMLFile, version=version, build=build)

    # Remove old HTMLFiles from ElasticSearch
    remove_indexed_files(
        model=HTMLFile,
        project_slug=version.project.slug,
        version_slug=version.slug,
        build_id=build,
    )

    # Delete SphinxDomain objects from previous versions
    # This has to be done before deleting ImportedFiles and not with a cascade,
    # because multiple Domain's can reference a specific HTMLFile.
    (
        SphinxDomain.objects
        .filter(project=version.project, version=version)
        .exclude(build=build)
        .delete()
    )

    # Delete ImportedFiles objects (including HTMLFiles)
    # from the previous build of the version.
    (
        ImportedFile.objects
        .filter(project=version.project, version=version)
        .exclude(build=build)
        .delete()
    )

    # Send signal with changed files
    files_changed.send(
        sender=Project,
        project=version.project,
        files=changed_files,
    )


@app.task(queue='web')
def send_notifications(version_pk, build_pk, email=False):
    version = Version.objects.get_object_or_log(pk=version_pk)

    if not version or version.type == EXTERNAL:
        return

    build = Build.objects.get(pk=build_pk)

    for hook in version.project.webhook_notifications.all():
        webhook_notification(version, build, hook.url)

    if email:
        for email_address in version.project.emailhook_notifications.all().values_list(
            'email',
            flat=True,
        ):
            email_notification(version, build, email_address)


def email_notification(version, build, email):
    """
    Send email notifications for build failure.

    :param version: :py:class:`Version` instance that failed
    :param build: :py:class:`Build` instance that failed
    :param email: Email recipient address
    """
    log.debug(
        LOG_TEMPLATE,
        {
            'project': version.project.slug,
            'version': version.slug,
            'msg': 'sending email to: %s' % email,
        }
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
            settings.PRODUCTION_DOMAIN,
            build.get_absolute_url(),
        ),
        'unsub_url': 'https://{}{}'.format(
            settings.PRODUCTION_DOMAIN,
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
            'commit': build.commit,
            'state': build.state,
            'success': build.success,
            'date': build.date.strftime('%Y-%m-%d %H:%M:%S'),
        },
    })
    log.debug(
        LOG_TEMPLATE,
        {
            'project': project.slug,
            'version': '',
            'msg': 'sending notification to: %s' % hook_url,
        }
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
        LOG_TEMPLATE,
        {
            'project': project.slug,
            'version': '',
            'msg': 'Updating static metadata',
        }
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
            LOG_TEMPLATE,
            {
                'project': project.slug,
                'version': '',
                'msg': 'Cannot write to metadata.json: {}'.format(e),
            }
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
def remove_build_storage_paths(paths):
    """
    Remove artifacts from build media storage (cloud or local storage).

    :param paths: list of paths in build media storage to delete
    """
    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
    for storage_path in paths:
        log.info('Removing %s from media storage', storage_path)
        storage.delete_directory(storage_path)


@app.task(queue='web')
def remove_search_indexes(project_slug, version_slug=None):
    """Wrapper around ``remove_indexed_files`` to make it a task."""
    remove_indexed_files(
        model=HTMLFile,
        project_slug=project_slug,
        version_slug=version_slug,
    )


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
    remove_search_indexes.delay(
        project_slug=project.slug,
        version_slug=version.slug if version else None,
    )


@app.task(queue='web')
def sync_callback(_, version_pk, commit, build, *args, **kwargs):
    """
    Called once the sync_files tasks are done.

    The first argument is the result from previous tasks, which we discard.
    """
    try:
        fileify(version_pk, commit=commit, build=build)
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


@app.task(queue='web')
def send_build_status(build_pk, commit, status):
    """
    Send Build Status to Git Status API for project external versions.

    :param build_pk: Build primary key
    :param commit: commit sha of the pull/merge request
    :param status: build status failed, pending, or success to be sent.
    """
    build = Build.objects.get(pk=build_pk)
    provider_name = build.project.git_provider_name

    if provider_name in [GITHUB_BRAND, GITLAB_BRAND]:
        # get the service class for the project e.g: GitHubService.
        service_class = build.project.git_service_class()
        try:
            service = service_class(
                build.project.remote_repository.users.first(),
                build.project.remote_repository.account
            )
            # Send status report using the API.
            service.send_build_status(build, commit, status)

        except RemoteRepository.DoesNotExist:
            users = build.project.users.all()

            # Try to loop through all project users to get their social accounts
            for user in users:
                user_accounts = service_class.for_user(user)
                # Try to loop through users all social accounts to send a successful request
                for account in user_accounts:
                    # Currently we only support GitHub Status API
                    if account.provider_name == provider_name:
                        success = account.send_build_status(build, commit, status)
                        if success:
                            return True

            for user in users:
                # Send Site notification about Build status reporting failure
                # to all the users of the project.
                notification = GitBuildStatusFailureNotification(
                    context_object=build.project,
                    extra_context={'provider_name': provider_name},
                    user=user,
                    success=False,
                )
                notification.send()

            log.info(
                'No social account or repository permission available for %s',
                build.project.slug
            )
            return False

        except Exception:
            log.exception('Send build status task failed for %s', build.project.slug)
            return False

    return False

    # TODO: Send build status for BitBucket.


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
