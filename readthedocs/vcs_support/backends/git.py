"""Git-related utilities."""

from __future__ import absolute_import

import csv
import logging
import os
import re

from builtins import str
from six import StringIO

from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion


log = logging.getLogger(__name__)


class Backend(BaseVCS):

    """Git VCS backend."""

    supports_tags = True
    supports_branches = True
    fallback_branch = 'master'  # default branch

    def __init__(self, *args, **kwargs):
        super(Backend, self).__init__(*args, **kwargs)
        self.token = kwargs.get('token', None)
        self.repo_url = self._get_clone_url()

    def _get_clone_url(self):
        if '://' in self.repo_url:
            hacked_url = self.repo_url.split('://')[1]
            hacked_url = re.sub('.git$', '', hacked_url)
            clone_url = 'https://%s' % hacked_url
            if self.token:
                clone_url = 'https://%s@%s' % (self.token, hacked_url)
                return clone_url
            # Don't edit URL because all hosts aren't the same

            # else:
                # clone_url = 'git://%s' % (hacked_url)
        return self.repo_url

    def set_remote_url(self, url):
        return self.run('git', 'remote', 'set-url', 'origin', url)

    def update(self):
        # Use checkout() to update repo
        self.checkout()

    def repo_exists(self):
        code, _, _ = self.run('git', 'status')
        return code == 0

    def fetch(self):
        code, _, _ = self.run('git', 'fetch', '--tags', '--prune')
        if code != 0:
            raise RepositoryError

    def checkout_revision(self, revision=None):
        if not revision:
            branch = self.default_branch or self.fallback_branch
            revision = 'origin/%s' % branch

        code, out, err = self.run('git', 'checkout',
                                  '--force', '--quiet', revision)
        if code != 0:
            log.warning("Failed to checkout revision '%s': %s",
                        revision, code)
        return [code, out, err]

    def clone(self):
        code, _, _ = self.run('git', 'clone', '--recursive', '--quiet',
                              self.repo_url, '.')
        if code != 0:
            raise RepositoryError

    @property
    def tags(self):
        retcode, stdout, _ = self.run('git', 'show-ref', '--tags')
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
        # StringIO below is expecting Unicode data, so ensure that it gets it.
        if not isinstance(data, str):
            data = str(data)
        raw_tags = csv.reader(StringIO(data), delimiter=' ')
        vcs_tags = []
        for row in raw_tags:
            row = [f for f in row if f != '']
            if row == []:
                continue
            commit_hash, name = row
            clean_name = name.split('/')[-1]
            vcs_tags.append(VCSVersion(self, commit_hash, clean_name))
        return vcs_tags

    @property
    def branches(self):
        # Only show remote branches
        retcode, stdout, _ = self.run('git', 'branch', '-r')
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_branches(stdout)

    def parse_branches(self, data):
        """
        Parse output of git branch -r

        e.g.:

              origin/2.0.X
              origin/HEAD -> origin/master
              origin/develop
              origin/master
              origin/release/2.0.0
              origin/release/2.1.0
        """
        clean_branches = []
        # StringIO below is expecting Unicode data, so ensure that it gets it.
        if not isinstance(data, str):
            data = str(data)
        raw_branches = csv.reader(StringIO(data), delimiter=' ')
        for branch in raw_branches:
            branch = [f for f in branch if f != '' and f != '*']
            # Handle empty branches
            if branch:
                branch = branch[0]
                if branch.startswith('origin/'):
                    cut_len = len('origin/')
                    slug = branch[cut_len:].replace('/', '-')
                    if slug in ['HEAD']:
                        continue
                    clean_branches.append(VCSVersion(self, branch, slug))
                else:
                    # Believe this is dead code.
                    slug = branch.replace('/', '-')
                    clean_branches.append(VCSVersion(self, branch, slug))
        return clean_branches

    @property
    def commit(self):
        _, stdout, _ = self.run('git', 'rev-parse', 'HEAD')
        return stdout.strip()

    def checkout(self, identifier=None):
        self.check_working_dir()

        # Clone or update repository
        if self.repo_exists():
            self.set_remote_url(self.repo_url)
            self.fetch()
        else:
            self.make_clean_working_dir()
            self.clone()

        # Find proper identifier
        if not identifier:
            identifier = self.default_branch or self.fallback_branch

        identifier = self.find_ref(identifier)

        # Checkout the correct identifier for this branch.
        code, out, err = self.checkout_revision(identifier)
        if code != 0:
            return code, out, err

        # Clean any remains of previous checkouts
        self.run('git', 'clean', '-d', '-f', '-f')

        # Update submodules
        self.run('git', 'submodule', 'sync')
        self.run('git', 'submodule', 'update',
                 '--init', '--recursive', '--force')

        return code, out, err

    def find_ref(self, ref):
        # Check if ref starts with 'origin/'
        if ref.startswith('origin/'):
            return ref

        # Check if ref is a branch of the origin remote
        if self.ref_exists('remotes/origin/' + ref):
            return 'origin/' + ref

        return ref

    def ref_exists(self, ref):
        code, _, _ = self.run('git', 'show-ref', ref)
        return code == 0

    @property
    def env(self):
        env = super(Backend, self).env
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        # Don't prompt for username, this requires Git 2.3+
        env['GIT_TERMINAL_PROMPT'] = '0'
        return env
