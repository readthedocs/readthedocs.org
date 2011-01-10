from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSTag

class Backend(BaseVCS):
    supports_tags = True
    
    def update(self):
        super(Backend, self).update()
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

    def get_tags(self):
        retcode, stdout = self._run_command('bzr', 'tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_tags(stdout)
    
    def _parse_tags(self, data):
        """
        Parses output of show-ref --tags, eg:
        
            0.1.0                171
            0.1.1                173
            0.1.2                174
            0.2.0-pre-alpha      177
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = [line.rsplit(' ', 1) for line in data.strip('\n').split('\n')]
        vcs_tags = []
        for name, commit in raw_tags:
            clean_name = name.strip(' ')
            vcs_tags.append(VCSTag(self, commit, clean_name))
        return vcs_tags
    
    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        if not identifier:
            self._up()
        else:
            self._run_command('hg', 'update', '-r', identifier)