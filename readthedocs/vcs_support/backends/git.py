# -*- coding: utf-8 -*-
"""Git-related utilities."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import csv
import logging
import os
import re

import git
from builtins import str
from django.core.exceptions import ValidationError
from git.exc import BadName
from six import PY2, StringIO

from readthedocs.config import ALL
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.validators import validate_submodule_url
from readthedocs.vcs_support.base import BaseVCS, VCSVersion

log = logging.getLogger(__name__)


class Backend(BaseVCS):

    """Git VCS backend."""

    supports_tags = True
    supports_branches = True
    supports_submodules = True
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
            #     clone_url = 'git://%s' % (hacked_url)
        return self.repo_url

    def set_remote_url(self, url):
        return self.run('git', 'remote', 'set-url', 'origin', url)

    def update(self):
        # Use checkout() to update repo
        # TODO: See where we call this
        self.checkout()

    def repo_exists(self):
        code, _, _ = self.run('git', 'status', record=False)
        return code == 0

    def are_submodules_available(self, config):
        """Test whether git submodule checkout step should be performed."""
        # TODO remove this after users migrate to a config file
        from readthedocs.projects.models import Feature
        submodules_in_config = (
            config.submodules.exclude != ALL or
            config.submodules.include
        )
        if (self.project.has_feature(Feature.SKIP_SUBMODULES) or
                not submodules_in_config):
            return False

        # Keep compatibility with previous projects
        code, out, _ = self.run('git', 'submodule', 'status', record=False)
        return code == 0 and bool(out)

    def validate_submodules(self, config):
        """
        Returns the submodules and check that its URLs are valid.

        .. note::

           Allways call after `self.are_submodules_available`.

        :returns: tuple(bool, list)

        Returns true if all required submodules URLs are valid.
        Returns a list of all required submodules:
        - Include is `ALL`, returns all submodules avaliable.
        - Include is a list, returns just those.
        - Exclude is `ALL` - this should never happen.
        - Exlude is a list, returns all avaliable submodules
          but those from the list.
        """
        repo = git.Repo(self.working_dir)
        submodules = {
            sub.path: sub
            for sub in repo.submodules
        }

        for sub_path in config.submodules.exclude:
            path = sub_path.rstrip('/')
            if path in submodules:
                del submodules[path]

        if config.submodules.include != ALL and config.submodules.include:
            submodules_include = {}
            for sub_path in config.submodules.include:
                path = sub_path.rstrip('/')
                submodules_include[path] = submodules[path]
            submodules = submodules_include

        for path, submodule in submodules.items():
            try:
                validate_submodule_url(submodule.url)
            except ValidationError:
                return False, []
        return True, submodules.keys()

    def fetch(self):
        code, _, _ = self.run('git', 'fetch', '--tags', '--prune')
        if code != 0:
            raise RepositoryError

    def checkout_revision(self, revision=None):
        if not revision:
            branch = self.default_branch or self.fallback_branch
            revision = 'origin/%s' % branch

        code, out, err = self.run('git', 'checkout', '--force', revision)
        if code != 0:
            log.warning("Failed to checkout revision '%s': %s", revision, code)
        return [code, out, err]

    def clone(self):
        """
        Clone the repository.

        .. note::

            Temporarily, we support skipping submodule recursive clone via a
            feature flag. This will eventually be configurable with our YAML
            config.
        """
        # TODO remove with https://github.com/rtfd/readthedocs-build/issues/30
        from readthedocs.projects.models import Feature
        cmd = ['git', 'clone']
        cmd.extend([self.repo_url, '.'])
        code, _, _ = self.run(*cmd)
        if code != 0:
            raise RepositoryError

    @property
    def tags(self):
        versions = []
        repo = git.Repo(self.working_dir)
        for tag in repo.tags:
            try:
                versions.append(VCSVersion(self, str(tag.commit), str(tag)))
            except ValueError as e:
                # ValueError: Cannot resolve commit as tag TAGNAME points to a
                # blob object - use the `.object` property instead to access it
                # This is not a real tag for us, so we skip it
                # https://github.com/rtfd/readthedocs.org/issues/4440
                log.warning('Git tag skipped: %s', tag, exc_info=True)
                continue
        return versions

    @property
    def branches(self):
        # Only show remote branches
        retcode, stdout, _ = self.run(
            'git',
            'branch',
            '-r',
            record_as_success=True,
        )
        # error (or no branches found)
        if retcode != 0:
            return []
        return self.parse_branches(stdout)

    def parse_branches(self, data):
        """
        Parse output of git branch -r.

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
        delimiter = str(' ').encode('utf-8') if PY2 else str(' ')
        raw_branches = csv.reader(StringIO(data), delimiter=delimiter)
        for branch in raw_branches:
            branch = [f for f in branch if f not in ('', '*')]
            # Handle empty branches
            if branch:
                branch = branch[0]
                if branch.startswith('origin/'):
                    verbose_name = branch.replace('origin/', '')
                    if verbose_name in ['HEAD']:
                        continue
                    clean_branches.append(
                        VCSVersion(self, branch, verbose_name))
                else:
                    clean_branches.append(VCSVersion(self, branch, branch))
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
        return code, out, err

    def update_submodules(self, config):
        if self.are_submodules_available(config):
            valid, submodules = self.validate_submodules(config)
            if valid:
                self.checkout_submodules(submodules, config)
            else:
                raise RepositoryError(RepositoryError.INVALID_SUBMODULES)

    def checkout_submodules(self, submodules, config):
        """Checkout all repository submodules."""
        self.run('git', 'submodule', 'sync')
        cmd = [
            'git',
            'submodule',
            'update',
            '--init',
            '--force',
        ]
        if config.submodules.recursive:
            cmd.append('--recursive')
        cmd += submodules
        self.run(*cmd)

    def find_ref(self, ref):
        # Check if ref starts with 'origin/'
        if ref.startswith('origin/'):
            return ref

        # Check if ref is a branch of the origin remote
        if self.ref_exists('remotes/origin/' + ref):
            return 'origin/' + ref

        return ref

    def ref_exists(self, ref):
        try:
            r = git.Repo(self.working_dir)
            if r.commit(ref):
                return True
        except (BadName, ValueError):
            return False
        return False

    @property
    def env(self):
        env = super(Backend, self).env
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        # Don't prompt for username, this requires Git 2.3+
        env['GIT_TERMINAL_PROMPT'] = '0'
        return env
