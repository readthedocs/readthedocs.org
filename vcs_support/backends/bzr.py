from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS


class Backend(BaseVCS):
    supports_tags = False
    
    def update(self):
        retcode = self._run_command('bzr', 'status')[0]
        if retcode == 0:
            self._up()
        else:
            self._checkout()
            
    def _up(self):
        retcode = self._run_command('bzr', 'revert')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (bzr revert): %s" % (self.repo_url, retcode)
            )
        retcode = self._run_command('bzr', 'up')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (bzr up): %s" % (self.repo_url, retcode)
            )
        
    def _checkout(self):
        retcode = self._run_command('bzr', 'checkout', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (bzr checkout): %s" % (self.repo_url, retcode)
            )