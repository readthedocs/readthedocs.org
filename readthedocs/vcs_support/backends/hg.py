import csv
from StringIO import StringIO

from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = True
    supports_branches = True
    fallback_branch = 'default'

    def update(self):
        super(Backend, self).update()
        retcode = self.run('hg', 'status')[0]
        if retcode == 0:
            return self.pull()
        else:
            return self.clone()

    def pull(self):
        pull_output = self.run('hg', 'pull')
        if output[0] != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg pull): %s" % (self.repo_url, retcode)
            )
        update_output = self.run('hg', 'update', '-C')[0]
        if update_output[0] != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg update): %s" % (self.repo_url, retcode)
            )
        return update_output

    def clone(self):
        output = self.run('hg', 'clone', self.repo_url, '.')
        if output[0] != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg clone): %s" % (self.repo_url, retcode)
            )
        return output

    @property
    def branches(self):
        retcode, stdout = self.run('hg', 'branches')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_branches(stdout)

    def parse_branches(self, data):
        """
        stable                     13575:8e94a1b4e9a4
        default                    13572:1bb2a56a9d73
        """
        raw_branches = csv.reader(StringIO(data), delimiter=' ')
        clean_branches = []
        for branch in raw_branches:
            branch = filter(lambda f: f != '', branch)
            if branch == []:
                continue
            name, rev = branch
            clean_branches.append(VCSVersion(self, name, name))
        return clean_branches

    @property
    def tags(self):
        retcode, stdout = self.run('hg', 'tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of show-ref --tags, eg:

        tip                              278:c4b2d21db51a
        0.2.2                            152:6b0364d98837
        0.2.1                            117:a14b7b6ffa03
        0.1                               50:30c2c6b3a055
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = csv.reader(StringIO(data), delimiter=' ')
        vcs_tags = []
        for row in raw_tags:
            row = filter(lambda f: f != '', row)
            if row == []:
                continue
            name, commit = row
            if name == 'tip':
                continue
            revision, commit_hash = commit.split(':')
            vcs_tags.append(VCSVersion(self, commit_hash, name))
        return vcs_tags

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        if not identifier:
            identifier = 'tip'
        retcode = self.run('hg', 'status')[0]
        if retcode == 0:
            self.run('hg', 'pull')
            return self.run('hg', 'update', '-C', identifier)
        else:
            self.clone()
            return self.run('hg', 'update', '-C', identifier)
