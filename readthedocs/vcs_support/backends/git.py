"""Git-related utilities."""

from __future__ import absolute_import

import csv
import logging
import os
import re

from builtins import str
from six import StringIO

from readthedocs.projects.exceptions import ProjectImportError
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
        code, _, err = self.run('git', 'fetch', '--tags', '--prune')
        if code != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (git fetch): %s\n\nStderr:\n\n%s\n\n" % (
                    self.repo_url, code, err)
            )

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
        code, _, err = self.run('git', 'clone', '--recursive', '--quiet',
                                self.repo_url, '.')
        if code != 0:
            raise ProjectImportError(
                (
                    "Failed to get code from '{url}' (git clone): {exit}\n\n"
                    "git clone error output: {sterr}"
                ).format(
                    url=self.repo_url,
                    exit=code,
                    sterr=err
                )
            )

    @property
    def tags(self):
        retcode, stdout, _ = self.run('git', 'show-ref', '--tags', '--dereference')
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of show-ref --tags --dereference, eg:

            8148e36c2d39600b3490d7b8186c4ece450f49bf refs/tags/4.2.1
            4d977eb02c9397a834825256544aaddfc62b8ea4 refs/tags/4.2.1^{}
            1f5a71b1000251084a29e425bfd2e9e1bdce2f9e refs/tags/5.0.0
            1ba246d740cd242e377d722630a909d85433c313 refs/tags/5.0.0^{}
            6bffaff0455f42530df688d23a73c21bc05e7703 refs/tags/5.0.0b1
            171a542f269aac28483a639b34ee56938f87577f refs/tags/5.0.0b1^{}
            4d17d4d5d6d2937c7b586acc34d23dcff1356fae refs/tags/5.0.0b2
            97bd1ea3260774ffe438a5f850c7873e903e6e3f refs/tags/5.0.0b2^{}
            fe8b7f362b9dc78bd15568912874a91b6ddeb8bb refs/tags/5.0.0rc1
            192b3e4c7a290ce87932965ab2d36343eea6dd19 refs/tags/5.0.0rc1^{}
            d1d50255fce289ba1effd52b83e0b905b579c86b refs/tags/5.1.0
            5c9c918bc0a11057184ec143da13b68994f59666 refs/tags/5.1.0^{}

        Label without ^{} points to hash that identifies git tag itself, and label
        with ^{} suffix points to specific commit that was marked with the tag.
        This prefixed label only appears for annotated tags.

        See https://www.kernel.org/pub/software/scm/git/docs/git-show-ref.html

        Returns sorted list of VCSVersion objects with the tag name as
        verbose_name and the commit hash as identifier.
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        # StringIO below is expecting Unicode data, so ensure that it gets it.
        if not isinstance(data, str):
            data = str(data)
        raw_tags = csv.reader(StringIO(data), delimiter=' ')
        # "tag name": "dereferenced commit hash"
        tag_map = dict()
        for row in raw_tags:
            # compress spaces
            row = [f for f in row if f != '']
            if row == []:
                continue
            # name includes ^{} suffix if any
            commit_hash, name = row
            clean_name = name.split('/')[-1].replace('^{}', '')
            dereferenced = name.endswith('^{}')
            if (clean_name not in tag_map) or (dereferenced):
                # dereferenced hash overwrites previous value
                tag_map[clean_name] = commit_hash
        vcs_tags = []
        for tag_name in sorted(tag_map):
            vcs_tags.append(VCSVersion(self, tag_map[tag_name], tag_name))
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
        return env
