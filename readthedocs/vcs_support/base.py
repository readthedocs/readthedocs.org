from django.utils.importlib import import_module
import os
import subprocess


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
        return "<VCSVersion: %s:%s" % (self.repository.repo_url, self.verbose_name)


class BaseCLI(object):
    """
    Helper class for CLI-heavy classes.
    """
    def _run_command(self, *bits):
        process = subprocess.Popen(bits, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=self.working_dir, shell=False,
            env=self.get_env())
        stdout, stderr = process.communicate()
        print "VCS: %s" % ' '.join(bits)
        return (process.returncode, stdout, stderr)

    def get_env(self):
        return os.environ.copy()


class BaseVCS(BaseCLI):
    supports_tags = False # Whether this VCS supports tags or not.
    supports_branches = False # Whether this VCS supports branches or not.
    contribution_backends = []

    #===========================================================================
    # General methods
    #===========================================================================

    def __init__(self, project):
        self.project =  project
        self.repo_url = project.repo
        self.working_dir = project.working_dir

    def _check_working_dir(self):
        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)

    def update(self):
        """
        If self.working_dir is already a valid local copy of the repository,
        update the repository, else create a new local copy of the repository.
        """
        self._check_working_dir()

    #===========================================================================
    # Tag / Branch related methods
    # These methods only apply if supports_tags = True and/or
    # support_branches = True
    #===========================================================================

    def get_tags(self):
        """
        Returns a list of VCSVersion objects. See VCSVersion for more information.
        """
        raise NotImplementedError

    def get_branches(self):
        """
        Returns a list of VCSVersion objects. See VCSVersion for more information.
        """
        raise NotImplementedError

    def checkout(self, identifier=None):
        """
        Set the state to the given identifier.

        If identifier is None, checkout to the latest revision.

        The type and format of identifier may change from VCS to VCS, so each
        backend is responsible to understand it's identifiers.
        """
        self._check_working_dir()

    #===========================================================================
    # Contribution related methods
    # These methods only apply if supports_contribution = True
    #===========================================================================

    def get_contribution_backend(self):
        """
        Returns a contribution backend or None for this repository. The backend
        is detected via the repository URL.
        """
        for backend in self.contribution_backends:
            if backend.accepts(self.repo_url):
                return backend(self)
        return None


class BaseContributionBackend(BaseCLI):
    """
    Base class for contribution backends.

    The main purpose of this base class is to define the API.
    """
    def __init__(self, repo):
        self.repo = repo
        self.project = repo.project
        self.repo_url = repo.repo_url
        self.working_dir = repo.working_dir

    @classmethod
    def accepts(cls, url):
        """
        Classmethod that checks if a given repository URL is supported by this
        backend.
        """
        return False

    def get_branch_file(self, branch, filename):
        """
        Returns the contents of a file as it is in the specified branch.
        """
        raise NotImplementedError

    def set_branch_file(self, branch, filename, contents, comment=''):
        """
        Saves the file in the specified branch.
        """
        raise NotImplementedError

    def push_branch(self, branch, title='', comment=''):
        """
        Pushes a branch upstream.
        """
        raise NotImplementedError

    def _open_file(self, filename, mode='r'):
        return open(os.path.join(self.repo.working_dir, filename), mode)


def get_backend(repo_type):
    try:
        module = import_module('vcs_support.backends.%s' % repo_type)
    except ImportError:
        return None
    return getattr(module, 'Backend', None)
