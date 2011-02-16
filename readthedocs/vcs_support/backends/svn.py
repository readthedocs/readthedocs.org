from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = False

    def __init__(self, project):
        super(Backend, self).__init__(project)
        if self.repo_url[-1] != '/':
            self.repo_url += '/'
        if self.repo_url.endswith('/trunk/'):
            self.supports_tags = True
            self.base_url = self.repo_url[:-7]

    def update(self):
        super(Backend, self).update()
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
            raise ProjectImportError(
                "Failed to get code from '%s' (svn revert): %s" % (self.repo_url, retcode)
            )
        retcode = self._run_command('svn', 'up', '--accept', 'theirs-full')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (svn up): %s" % (self.repo_url, retcode)
            )

    def _co(self):
        retcode = self._run_command('svn', 'checkout', '--quiet', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (svn checkout): %s" % (self.repo_url, retcode)
            )

    def get_tags(self):
        retcode, stdout = self._run_command('svn', 'list', '%s/tags/' % self.base_url)[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_tags(stdout)

    def _parse_tags(self, data):
        """
        Parses output of svn list, eg:

            release-1.1/
            release-1.2/
            release-1.3/
            release-1.4/
            release-1.4.1/
            release-1.5/
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = [line.rstrip('/') for line in data.strip('\n').split('\n')]
        vcs_tags = []
        for name in raw_tags:
            vcs_tags.append(VCSVersion(self, '/tags/%s/' % name, name))
        return vcs_tags

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        if not identifier:
            identifier = '/trunk/'
        self._run_command('svn', 'switch', '%s%s' % (self.base_url, identifier))
