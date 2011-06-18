import os
from os.path import join as pjoin

from projects.exceptions import ProjectImportError
from projects.tasks import remove_dir
from vcs_support.backends.github import GithubContributionBackend
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = True
    supports_branches = True
    contribution_backends = [GithubContributionBackend]
    fallback_branch = 'master' # default branch

    def _check_working_dir(self):
        code, out, err = self._run_command(
            'git', 'config', '-f',
            pjoin(self.working_dir, '.git/config'),
            '--get', 'remote.origin.url')

        if out.strip() != self.repo_url:
            remove_dir(self.working_dir)
        super(Backend, self)._check_working_dir()

    def update(self):
        super(Backend, self).update()
        retcode = self._run_command('git', 'status')[0]
        if retcode == 0:
            self._pull()
        else:
            self._clone()
        self._run_command('git', 'submodule', 'update', '--init')
        self._reset()

    def _pull(self):
        retcode = self._run_command('git', 'fetch')[0]
        retcode = self._run_command('git', 'fetch', '-t')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s" % (self.repo_url, retcode)
            )

    def _reset(self):
        branch = self.fallback_branch
        if self.project.default_branch:
            branch = self.project.default_branch
        retcode = self._run_command('git', 'reset', '--hard', 'origin/%s' % branch)[0]
        if retcode != 0:
            print "Failed to get code from '%s' (git reset): %s" % (self.repo_url, retcode)
            print "Going on because this might not be horrible."
            #raise ProjectImportError(
                #"Failed to get code from '%s' (git reset): %s" % (self.repo_url, retcode)
            #)

    def _clone(self):
        retcode = self._run_command('git', 'clone', '--quiet', '%s.git' % self.repo_url.replace('.git', ''), '.')[0]
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
            vcs_tags.append(VCSVersion(self, commit_hash, clean_name))
        return vcs_tags

    def get_branches(self):
        retcode, stdout = self._run_command('git', 'branch', '-a')[:2]
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
        raw_branches = [bit[2:] for bit in data.split('\n') if bit.strip()]
        clean_branches = []
        for branch in raw_branches:
            if branch.startswith('remotes/'):
                if branch.startswith('remotes/origin/'):
                    real_branch = branch.split(' ')[0]
                    slug = real_branch[15:].replace('/', '-')
                    if slug in ['HEAD', self.fallback_branch]:
                        continue
                    clean_branches.append(VCSVersion(self, real_branch, slug))
            else:
                clean_branches.append(VCSVersion(self, branch, branch))
        return clean_branches

    def _get_clean_tag_name(self, name):
        return name.split('/', 2)[2]

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        #Run update so that we can pull new versions.
        self.update()
        if not identifier:
            identifier = self.fallback_branch
            if self.project.default_branch:
                identifier = self.project.default_branch
        #Checkout the correct identifier for this branch.
        self._run_command('git', 'reset', '--hard', identifier)

    def get_env(self):
        env = super(Backend, self).get_env()
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        return env
