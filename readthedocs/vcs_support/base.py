# -*- coding: utf-8 -*-
"""Base classes for VCS backends."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import os
import shutil

from builtins import object

log = logging.getLogger(__name__)


class VCSVersion(object):

    """
    Represents a Version (tag or branch) in a VCS.

    This class should only be instantiated in BaseVCS subclasses.

    It can act as a context manager to temporarily switch to this tag (eg to
    build docs for this tag).
    """

    def __init__(self, repository, identifier, verbose_name):
        self.repository = repository
        self.identifier = identifier
        self.verbose_name = verbose_name

    def __repr__(self):
        return '<VCSVersion: %s:%s' % (
            self.repository.repo_url, self.verbose_name)


class BaseVCS(object):

    """
    Base for VCS Classes.

    VCS commands are ran inside a ``LocalEnvironment``.
    """

    supports_tags = False  # Whether this VCS supports tags or not.
    supports_branches = False  # Whether this VCS supports branches or not.
    supports_submodules = False

    # =========================================================================
    # General methods
    # =========================================================================

    # Defining a base API, so we'll have unused args
    # pylint: disable=unused-argument
    def __init__(self, project, version_slug, environment=None, **kwargs):
        self.default_branch = project.default_branch
        self.project = project
        self.name = project.name
        self.repo_url = project.clean_repo
        self.working_dir = project.checkout_path(version_slug)

        from readthedocs.doc_builder.environments import LocalEnvironment
        self.environment = environment or LocalEnvironment(project)

        # Update the env variables with the proper VCS env variables
        self.environment.environment.update(self.env)

    def check_working_dir(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

    def make_clean_working_dir(self):
        """Ensures that the working dir exists and is empty."""
        shutil.rmtree(self.working_dir, ignore_errors=True)
        self.check_working_dir()

    @property
    def env(self):
        environment = os.environ.copy()

        # TODO: kind of a hack
        del environment['PATH']

        return environment

    def update(self):
        """
        Update a local copy of the repository in self.working_dir.

        If self.working_dir is already a valid local copy of the repository,
        update the repository, else create a new local copy of the repository.
        """
        self.check_working_dir()

    def run(self, *cmd, **kwargs):
        kwargs.update({
            'cwd': self.working_dir,
            'shell': False,
        })

        build_cmd = self.environment.run(*cmd, **kwargs)
        # Return a tuple to keep compatibility
        return (build_cmd.exit_code, build_cmd.output, build_cmd.error)

    # =========================================================================
    # Tag / Branch related methods
    # These methods only apply if supports_tags = True and/or
    # support_branches = True
    # =========================================================================

    @property
    def tags(self):
        """
        Returns a list of VCSVersion objects.

        See VCSVersion for more information.
        """
        raise NotImplementedError

    @property
    def branches(self):
        """
        Returns a list of VCSVersion objects.

        See VCSVersion for more information.
        """
        raise NotImplementedError

    @property
    def commit(self):
        """Returns a string representing the current commit."""
        raise NotImplementedError

    def checkout(self, identifier=None):
        """
        Set the state to the given identifier.

        If identifier is None, checkout to the latest revision.

        The type and format of identifier may change from VCS to VCS, so each
        backend is responsible to understand it's identifiers.
        """
        self.check_working_dir()

    def update_submodules(self, config):
        """
        Update the submodules of the current checkout.

        :type config: readthedocs.config.BuildConfigBase
        """
        raise NotImplementedError
