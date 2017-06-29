"""Base classes for VCS backends."""
from __future__ import absolute_import
from builtins import object
import logging
import os
import shutil
import subprocess
from collections import namedtuple
from os.path import basename


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
        return "<VCSVersion: %s:%s" % (self.repository.repo_url,
                                       self.verbose_name)


class VCSProject(namedtuple("VCSProject",
                            "name default_branch working_dir repo_url")):

    """Transient object to encapsulate a projects stuff"""

    pass


class BaseCLI(object):

    """Helper class for CLI-heavy classes."""

    log_tmpl = u'VCS[{name}:{ident}]: {args}'

    def __call__(self, *args):
        return self.run(args)

    def run(self, *args):
        """:param bits: list of command and args. See `subprocess` docs"""
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=self.working_dir, shell=False,
                                   env=self.env)
        try:
            log.info(self.log_tmpl.format(ident=basename(self.working_dir),
                                          name=self.name,
                                          args=' '.join(args)))
        except UnicodeDecodeError:
            # >:x
            pass
        stdout, stderr = process.communicate()
        try:
            log.info(self.log_tmpl.format(ident=basename(self.working_dir),
                                          name=self.name,
                                          args=stdout))
        except UnicodeDecodeError:
            # >:x
            pass
        return (process.returncode, stdout, stderr)

    @property
    def env(self):
        return os.environ.copy()


class BaseVCS(BaseCLI):

    """
    Base for VCS Classes.

    Built on top of the BaseCLI.
    """

    supports_tags = False  # Whether this VCS supports tags or not.
    supports_branches = False  # Whether this VCS supports branches or not.

    # =========================================================================
    # General methods
    # =========================================================================

    # Defining a base API, so we'll have unused args
    # pylint: disable=unused-argument
    def __init__(self, project, version, **kwargs):
        self.default_branch = project.default_branch
        self.name = project.name
        self.repo_url = project.repo_url
        self.working_dir = project.working_dir

    def check_working_dir(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

    def make_clean_working_dir(self):
        """Ensures that the working dir exists and is empty"""
        shutil.rmtree(self.working_dir, ignore_errors=True)
        self.check_working_dir()

    def update(self):
        """
        Update a local copy of the repository in self.working_dir.

        If self.working_dir is already a valid local copy of the repository,
        update the repository, else create a new local copy of the repository.
        """
        self.check_working_dir()

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
