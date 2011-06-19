import csv
import os
from StringIO import StringIO

from projects.exceptions import ProjectImportError
from vcs_support.backends.github import GithubContributionBackend
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = True
    supports_branches = True
    contribution_backends = [GithubContributionBackend]
    fallback_branch = 'master' # default branch

    def update(self):
        super(Backend, self).update()
        code, out, err = self.run('git', 'status')
        if code == 0:
            self._pull()
        else:
            self._clone()
        self.run('git', 'submodule', 'update', '--init')
        self._reset()

    def _pull(self):
        code, out, err = self.run('git', 'fetch')
        code, out, err = self.run('git',  'fetch', '-t')
        if code != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s" % (
                    self.repo_url, code)
            )

    def _reset(self):
        branch = self.fallback_branch
        if self.project.default_branch:
            branch = self.project.default_branch
        code, out, err = self.run('git', 'reset', '--hard',
                                  'origin/%s' % branch)
        if code != 0:
            print "Failed to get code from '%s' (git reset): %s" % (
                self.repo_url, code)
            print "Going on because this might not be horrible."
            #raise ProjectImportError(
                #"Failed to get code from '%s' (git reset): %s" % (self.repo_url, retcode)
            #)

    def _clone(self):
        code, out, err = self.run('git', 'clone', '--quiet',
                                  self.repo_url, '.')
        if code != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git clone): %s" % (
                    self.repo_url, code)
            )

    @property
    def tags(self):
        retcode, stdout, err = self.run('git', 'show-ref', '--tags')
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

        raw_tags = csv.reader(StringIO(data), delimiter=' ')
        vcs_tags = []

        for commit_hash, name in raw_tags:
            clean_name = name.split('/')[-1]
            vcs_tags.append(VCSVersion(self, commit_hash, clean_name))
        return vcs_tags

    @property
    def branches(self):
        retcode, stdout, err = self.run('git', 'branch', '-a')
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_branches(stdout)

    def _parse_branches(self, data):
        """
        Parse output of git branch -a, eg:
              develop
              master
            * release/2.0.0
              rtd-jonas
              remotes/origin/2.0.X
              remotes/origin/HEAD -> origin/master
              remotes/origin/develop
              remotes/origin/master
              remotes/origin/release/2.0.0
              remotes/origin/release/2.1.0
        """
        raw_branches = csv.reader(StringIO(data), delimiter=' ')
        clean_branches = []
        for branch in raw_branches:
            branch = branch[-1]
            if branch.startswith('remotes/origin/'):
                real_branch = branch.split(' ')[0]
                slug = real_branch[15:].replace('/', '-')
                if slug in ['HEAD', self.fallback_branch]:
                    continue
                clean_branches.append(VCSVersion(self, real_branch, slug))
            else:
                clean_branches.append(VCSVersion(self, branch, branch))
        return clean_branches

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        #Run update so that we can pull new versions.
        self.update()
        if not identifier:
            identifier = self.fallback_branch
            if self.project.default_branch:
                identifier = self.project.default_branch
        #Checkout the correct identifier for this branch.
        self.run('git', 'reset', '--hard', identifier)

    @property
    def env(self):
        env = super(Backend, self).env
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env
