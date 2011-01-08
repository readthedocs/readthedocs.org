from django.utils.importlib import import_module
import os
import subprocess


class VCSTag(object):
    """
    Represents a Tag in a VCS.
    
    This class should only be instantiated in BaseVCS subclasses.
    
    It can act as a context manager to temporarily switch to this tag (eg to
    build docs for this tag).
    """
    def __init__(self, repository, identifier, verbose_name):
        self.repository = repository
        self.identifier = identifier
        self.verbose_name = verbose_name
        
    def __enter__(self):
        self.repository.checkout(self.identifier)
        
    def __exit__(self):
        self.repository.checkout()
        
    def __repr__(self):
        return "<VCSTag: %s:%s" % (self.repository.repo_url, self.verbose_name)


class BaseVCS(object):
    supports_tags = False # Whether this VCS supports tags or not.
    
    #===========================================================================
    # General Methods
    #===========================================================================
    
    def __init__(self, repo_url, working_dir):
        self.repo_url = repo_url
        self.working_dir = working_dir
        
    def update(self):
        """
        If self.working_dir is already a valid local copy of the repository,
        update the repository, else create a new local copy of the repository.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Tag related Methods 
    # These methods only apply if support_tags = True
    #===========================================================================
    
    def get_tags(self):
        """
        Returns a list of VCSTag objects. See VCSTag for more information.
        """
        raise NotImplementedError
    
    def checkout(self, identifier=None):
        """
        Set the state to the given identifier.
        
        If identifier is None, checkout to the latest revision.
        
        The type and format of identifier may change from VCS to VCS, so each
        backend is responsible to understand it's identifiers. 
        """
        raise NotImplementedError
    
    #===========================================================================
    # Helper Methods
    #===========================================================================
    
    def _run_command(self, *bits):
        process = subprocess.Popen(bits, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=self.working_dir, shell=False,
            env=self.get_env())
        stdout, stderr = process.communicate()
        return (process.returncode, stdout, stderr)
    
    def get_env(self):
        return os.environ.copy()


def get_backend(repo_type):
    try:
        module = import_module('vcs_support.backends.%s' % repo_type)
    except ImportError:
        return None
    return getattr(module, 'Backend', None)