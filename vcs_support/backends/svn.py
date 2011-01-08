from projects.tasks import ProjectImportError
from vcs_support.backends.base import BaseVCS


class Backend(BaseVCS):
    supports_tags = False
    
    def update(self):
        # For some reason `svn status` gives me retcode 0 in non-svn directories
        # that's why I use `svn info` here.
        retcode = self._run_command('svn', 'info')[0]
        if retcode == 0:
            self._up()
        else:
            self._co()
            
    def _up(self):
        retcode = self._run_command('svn', 'revert', '--recursive', '.')[0]
        if retcode != 0:
            raise ProjectImportError("Failed to get code from '%s' (svn revert)" % self.repo_url)
        retcode = self._run_command('svn', 'up', '--accept', 'theirs-full')[0]
        if retcode != 0:
            raise ProjectImportError("Failed to get code from '%s' (svn up)" % self.repo_url)
        
    def _co(self):
        retcode = self._run_command('svn', 'checkout', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError("Failed to get code from '%s' (svn checkout)" % self.repo_url)