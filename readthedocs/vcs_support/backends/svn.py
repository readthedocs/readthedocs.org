import csv
from StringIO import StringIO

from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = False
    fallback_branch = '/trunk/'

    def __init__(self, project, version):
        super(Backend, self).__init__(project, version)
        if self.repo_url[-1] != '/':
            self.base_url = self.repo_url
            self.repo_url += '/'
        elif self.repo_url.endswith('/trunk/'):
            self.supports_tags = True
            self.base_url = self.repo_url[:-7]
        else:
            self.base_url = self.repo_url

    def update(self):
        super(Backend, self).update()
        # For some reason `svn status` gives me retcode 0 in non-svn directories
        # that's why I use `svn info` here.
        retcode = self.run('svn', 'info')[0]
        if retcode == 0:
            self.up()
        else:
            self.co()

    def up(self):
        retcode = self.run('svn', 'revert', '--recursive', '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (svn revert): %s" % (self.repo_url, retcode)
            )
        retcode = self.run('svn', 'up', '--accept', 'theirs-full', '--trust-server-cert', '--non-interactive')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (svn up): %s" % (self.repo_url, retcode)
            )

    def co(self, identifier=None):
        if identifier:
            url = self.base_url + identifier
        else:
            url = self.repo_url
        retcode = self.run('svn', 'checkout', '--quiet', url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (svn checkout): %s" % (url, retcode)
            )

    @property
    def tags(self):
        retcode, stdout = self.run('svn', 'list', '%s/tags/' % self.base_url)[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
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

        raw_tags = csv.reader(StringIO(data), delimiter='/')
        vcs_tags = []
        for name, _ in raw_tags:
            vcs_tags.append(VCSVersion(self, '/tags/%s/' % name, name))
        return vcs_tags

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        retcode = self.run('svn', 'info')[0]
        if retcode == 0:
            self.up()
        else:
            self.co(identifier)
