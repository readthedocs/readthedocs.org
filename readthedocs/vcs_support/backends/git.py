import logging
import csv
import os
from os.path import exists, join as pjoin
from StringIO import StringIO
from shutil import rmtree

from projects.exceptions import ProjectImportError
from vcs_support.backends.github import GithubContributionBackend
from vcs_support.base import BaseVCS, VCSVersion

log = logging.getLogger(__name__)


class Backend(BaseVCS):
    supports_tags = True
    supports_branches = True
    contribution_backends = [GithubContributionBackend]
    fallback_branch = 'master'  # default branch

    def check_working_dir(self):
        if exists(self.working_dir):
            code, out, err = self.run('git', 'config', '-f',
                                      pjoin(self.working_dir, '.git/config'),
                                      '--get', 'remote.origin.url')
            if out.strip() != self.repo_url:
                rmtree(self.working_dir)
        super(Backend, self).check_working_dir()

    def update(self):
        super(Backend, self).update()
        code, out, err = self.run('git', 'status')
        if code == 0:
            self.pull()
        else:
            self.clone()
        self.run('git', 'submodule', 'sync')
        self.run('git', 'submodule', 'update', '--init', '--recursive')
        return self.reset()

    def pull(self):
        code, out, err = self.run('git', 'fetch')
        code, out, err = self.run('git',  'fetch', '-t')
        if code != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s" % (
                    self.repo_url, code)
            )

    def reset(self):
        branch = self.fallback_branch
        if self.default_branch:
            branch = self.default_branch
        code, out, err = self.run('git', 'reset', '--hard',
                                  'origin/%s' % branch)
        if code != 0:
            log.warning("Failed to get code from '%s' (git reset): %s" % (
                self.repo_url, code))
        return [code, out, err]

    def clone(self):
        code, out, err = self.run('git', 'clone', '--recursive', '--quiet',
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
        return self.parse_tags(stdout)

    def parse_tags(self, data):
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
        for row in raw_tags:
            row = filter(lambda f: f != '', row)
            if row == []:
                continue
            commit_hash, name = row
            clean_name = name.split('/')[-1]
            vcs_tags.append(VCSVersion(self, commit_hash, clean_name))
        return vcs_tags

    @property
    def branches(self):
        retcode, stdout, err = self.run('git', 'branch', '-a')
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_branches(stdout)

    def parse_branches(self, data):
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
        clean_branches = []
        raw_branches = csv.reader(StringIO(data), delimiter=' ')
        for branch in raw_branches:
            branch = filter(lambda f: f != '' and f != '*', branch)
            branch = branch[0]
            if branch.startswith('remotes/origin/'):
                slug = branch[15:].replace('/', '-')
                if slug in ['HEAD', self.fallback_branch]:
                    continue
                clean_branches.append(VCSVersion(self, branch, slug))
            else:
                slug = branch.replace('/', '-')
                clean_branches.append(VCSVersion(self, branch, slug))
        return clean_branches

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        #Run update so that we can pull new versions.
        self.update()
        if not identifier:
            identifier = self.fallback_branch
            if self.default_branch:
                identifier = self.default_branch
        #Checkout the correct identifier for this branch.
        return self.run('git', 'reset', '--hard', identifier, '--')

    @property
    def env(self):
        env = super(Backend, self).env
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env
