from projects.exceptions import ProjectImportError
from vcs_support.backends.github import GithubContributionBackend
from vcs_support.base import BaseVCS, VCSTag
import os
        

class Backend(BaseVCS):
    supports_tags = True
    contribution_backends = [GithubContributionBackend]
    
    def update(self):
        retcode = self._run_command('git', 'status')[0]
        if retcode == 0:
            self._pull()
        else:
            self._clone()
            
    def _pull(self):
        retcode = self._run_command('git', 'fetch')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s" % (self.repo_url, retcode)
            )
        retcode = self._run_command('git', 'reset', '--hard', 'origin/master')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git reset): %s" % (self.repo_url, retcode)
            )
        
    def _clone(self):
        retcode = self._run_command('git', 'clone', '--quiet', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git clone): %s" % (self.repo_url, retcode)
            )
    
    def get_tags(self):
        retcode, stdout = self._run_command('git', 'show-ref', '--tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_tags(stdout)
    
    def _parse_tags(self, data):
        """
        Parses output of show-ref --tags, eg:
        
            3b32886c8d3cb815df3793b3937b2e91d0fb00f1 refs/tags/2.0.0
            bd533a768ff661991a689d3758fcfe72f455435d refs/tags/2.0.1
            c0288a17899b2c6818f74e3a90b77e2a1779f96a refs/tags/2.0.2
            a63a2de628a3ce89034b7d1a5ca5e8159534eef0 refs/tags/2.1.0.beta2
            c7fc3d16ed9dc0b19f0d27583ca661a64562d21e refs/tags/2.1.0.rc1
            edc0a2d02a0cc8eae8b67a3a275f65cd126c05b1 refs/tags/2.1.0.rc2
        
        Into VCSTag objects with the tag name as verbose_name and the commit
        hash as identifier.
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = [line.split(' ', 1) for line in data.strip('\n').split('\n')]
        vcs_tags = []
        for commit_hash, name in raw_tags:
            clean_name = self._get_clean_tag_name(name)
            vcs_tags.append(VCSTag(self, commit_hash, clean_name))
        return vcs_tags
    
    def _get_clean_tag_name(self, name):
        return name.split('/', 2)[2]
    
    def checkout(self, identifier=None):
        if not identifier:
            identifier = 'master'
        self._run_command('git', 'reset', '--hard', identifier)
        
    def get_env(self):
        env = super(Backend, self).get_env()
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env