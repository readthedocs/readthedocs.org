import datetime
import json
import os
import signal
import socket
import tarfile
import tempfile
from collections import Counter, defaultdict

from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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
from readthedocs.doc_builder.environments import (
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.search.utils import index_new_files, remove_indexed_files
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.storage import build_environment_storage, build_media_storage
from readthedocs.worker import app

from ..models import APIProject, Feature, WebHookEvent
from ..models import HTMLFile, ImportedFile, Project
from ..signals import (
    after_build,
    before_build,
    before_vcs,
    files_changed,
)
from ..exceptions import RepositoryError

log = structlog.get_logger(__name__)


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
        version_repo = self.data.project.vcs_repo(
            version=self.data.version.slug,
            environment=environment,
            verbose_name=self.data.version.verbose_name,
            version_type=self.data.version.type
        )
        return version_repo

    def sync_repo(self, environment):
        """Update the project's repository and hit ``sync_versions`` API."""
        # Make Dirs
        if not os.path.exists(self.data.project.doc_path):
            os.makedirs(self.data.project.doc_path)

        if not self.data.project.vcs_class():
            raise RepositoryError(
                _('Repository type "{repo_type}" unknown').format(
                    repo_type=self.data.project.repo_type,
                ),
            )

        # Get the actual code on disk
        log.info(
            'Checking out version.',
            version_identifier=self.data.version.identifier,
        )
        version_repo = self.get_vcs_repo(environment)
        version_repo.update()
        self.sync_versions(version_repo)
        identifier = self.data.build_commit or self.data.version.identifier
        version_repo.checkout(identifier)

    def sync_versions(self, version_repo):
        """
        Update tags/branches via a Celery task.

        .. note::

           It may trigger a new build to the stable version.
        """
        tags = None
        branches = None
        if (
            version_repo.supports_lsremote and
            not version_repo.repo_exists() and
            self.data.project.has_feature(Feature.VCS_REMOTE_LISTING)
        ):
            # Do not use ``ls-remote`` if the VCS does not support it or if we
            # have already cloned the repository locally. The latter happens
            # when triggering a normal build.
            branches, tags = version_repo.lsremote
            log.info('Remote versions.', branches=branches, tags=tags)

        branches_data = []
        tags_data = []

        if (
            version_repo.supports_tags and
            not self.data.project.has_feature(Feature.SKIP_SYNC_TAGS)
        ):
            # Will be an empty list if we called lsremote and had no tags returned
            if tags is None:
                tags = version_repo.tags
            tags_data = [
                {
                    'identifier': v.identifier,
                    'verbose_name': v.verbose_name,
                }
                for v in tags
            ]

        if (
            version_repo.supports_branches and
            not self.data.project.has_feature(Feature.SKIP_SYNC_BRANCHES)
        ):
            # Will be an empty list if we called lsremote and had no branches returned
            if branches is None:
                branches = version_repo.branches
            branches_data = [
                {
                    'identifier': v.identifier,
                    'verbose_name': v.verbose_name,
                }
                for v in branches
            ]

        self.validate_duplicate_reserved_versions(
            tags_data=tags_data,
            branches_data=branches_data,
        )

        build_tasks.sync_versions_task.delay(
            project_pk=self.data.project.pk,
            tags_data=tags_data,
            branches_data=branches_data,
        )

    def validate_duplicate_reserved_versions(self, tags_data, branches_data):
        """
        Check if there are duplicated names of reserved versions.

        The user can't have a branch and a tag with the same name of
        ``latest`` or ``stable``. Raise a RepositoryError exception
        if there is a duplicated name.

        :param data: Dict containing the versions from tags and branches
        """
        version_names = [
            version['verbose_name']
            for version in tags_data + branches_data
        ]
        counter = Counter(version_names)
        for reserved_name in [STABLE_VERBOSE_NAME, LATEST_VERBOSE_NAME]:
            if counter[reserved_name] > 1:
                raise RepositoryError(
                    RepositoryError.DUPLICATED_RESERVED_VERSIONS,
                )

    def get_vcs_env_vars(self):
        """Get environment variables to be included in the VCS setup step."""
        env = self.get_rtd_env_vars()
        # Don't prompt for username, this requires Git 2.3+
        env['GIT_TERMINAL_PROMPT'] = '0'
        return env

    def get_rtd_env_vars(self):
        """Get bash environment variables specific to Read the Docs."""
        env = {
            'READTHEDOCS': 'True',
            'READTHEDOCS_VERSION': self.data.version.slug,
            'READTHEDOCS_VERSION_TYPE': self.data.version.type,
            'READTHEDOCS_VERSION_NAME': self.data.version.verbose_name,
            'READTHEDOCS_PROJECT': self.data.project.slug,
            'READTHEDOCS_LANGUAGE': self.data.project.language,
        }
        return env
