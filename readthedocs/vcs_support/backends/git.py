# -*- coding: utf-8 -*-

"""Git-related utilities."""

import logging
import os
import re
import json
from django.conf import settings

import git
from django.core.exceptions import ValidationError
from git.exc import BadName, InvalidGitRepositoryError

from readthedocs.builds.constants import EXTERNAL
from readthedocs.config import ALL
from readthedocs.projects.constants import (
    GITHUB_BRAND,
    GITHUB_PR_PULL_PATTERN,
    GITLAB_BRAND,
    GITLAB_MR_PULL_PATTERN,
)
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.validators import validate_submodule_url
from readthedocs.vcs_support.base import BaseVCS, VCSVersion
from collections import namedtuple


log = logging.getLogger(__name__)


RepoInformation = namedtuple('RepoInformation', 'commit branches tags submodules')


class Backend(BaseVCS):

    """Git VCS backend."""

    supports_tags = True
    supports_branches = True
    supports_submodules = True
    fallback_branch = 'master'  # default branch
    repo_depth = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = kwargs.get('token', None)
        self.repo_url = self._get_clone_url()

    def _get_clone_url(self):
        if '://' in self.repo_url:
            hacked_url = self.repo_url.split('://')[1]
            hacked_url = re.sub('.git$', '', hacked_url)
            clone_url = 'https://%s' % hacked_url
            if self.token:
                clone_url = 'https://{}@{}'.format(self.token, hacked_url)
                return clone_url
            # Don't edit URL because all hosts aren't the same
            # else:
            #     clone_url = 'git://%s' % (hacked_url)
        return self.repo_url

    def _get_repo_info(self):
        cache_key = '__repo_info'
        repo_info = getattr(self, cache_key)
        if repo_info:
            return repo_info

        cmd = [
            'python3',
            '-m',
            'pip',
            'install',
            '--user',
            'GitPython==3.0.3',
        ]
        code, *_ = self.run(*cmd)
        if code != 0:
            raise RepositoryError

        cmd = [
            'python3',
            os.path.join(
                settings.RTD_SCRIPTS_PATH,
                'get_vcs_info.py',
            ),
            self.working_dir,
        ]
        code, stdout, stderr = self.run(*cmd)
        if code != 0:
            raise RepositoryError(stderr)
        repo_info = RepoInformation(**json.loads(stdout))
        setattr(self, cache_key, repo_info)
        return repo_info

    def set_remote_url(self, url):
        return self.run('git', 'remote', 'set-url', 'origin', url)

    def update(self):
        """Clone or update the repository."""
        super().update()
        if self.repo_exists():
            self.set_remote_url(self.repo_url)
            return self.fetch()
        self.make_clean_working_dir()
        # A fetch is always required to get external versions properly
        if self.version_type == EXTERNAL:
            self.clone()
            return self.fetch()
        return self.clone()

    def repo_exists(self):
        try:
            self._get_repo_info()
        except RepositoryError:
            return False
        return True

    def are_submodules_available(self, config):
        """Test whether git submodule checkout step should be performed."""
        submodules_in_config = (
            config.submodules.exclude != ALL or config.submodules.include
        )
        if not submodules_in_config:
            return False

        # Keep compatibility with previous projects
        return bool(self._get_repo_info().submodules)

    def validate_submodules(self, config):
        """
        Returns the submodules and check that its URLs are valid.

        .. note::

           Allways call after `self.are_submodules_available`.

        :returns: tuple(bool, list)

        Returns `True` if all required submodules URLs are valid.
        Returns a list of all required submodules:
        - Include is `ALL`, returns all submodules available.
        - Include is a list, returns just those.
        - Exclude is `ALL` - this should never happen.
        - Exlude is a list, returns all available submodules
          but those from the list.

        Returns `False` if at least one submodule is invalid.
        Returns the list of invalid submodules.
        """
        submodules = {sub.path: sub for sub in self.submodules}

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

        invalid_submodules = []
        for path, submodule in submodules.items():
            try:
                validate_submodule_url(submodule.url)
            except ValidationError:
                invalid_submodules.append(path)

        if invalid_submodules:
            return False, invalid_submodules
        return True, submodules.keys()

    def use_shallow_clone(self):
        """
        Test whether shallow clone should be performed.

        .. note::

            Temporarily, we support skipping this option as builds that rely on
            git history can fail if using shallow clones. This should
            eventually be configurable via the web UI.
        """
        from readthedocs.projects.models import Feature
        return not self.project.has_feature(Feature.DONT_SHALLOW_CLONE)

    def fetch(self):
        # --force lets us checkout branches that are not fast-forwarded
        # https://github.com/readthedocs/readthedocs.org/issues/6097
        cmd = ['git', 'fetch', 'origin',
               '--force', '--tags', '--prune', '--prune-tags']

        if self.use_shallow_clone():
            cmd.extend(['--depth', str(self.repo_depth)])

        if self.verbose_name and self.version_type == EXTERNAL:

            if self.project.git_provider_name == GITHUB_BRAND:
                cmd.append(
                    GITHUB_PR_PULL_PATTERN.format(id=self.verbose_name)
                )

            if self.project.git_provider_name == GITLAB_BRAND:
                cmd.append(
                    GITLAB_MR_PULL_PATTERN.format(id=self.verbose_name)
                )

        code, stdout, stderr = self.run(*cmd)
        if code != 0:
            raise RepositoryError

        return code, stdout, stderr

    def checkout_revision(self, revision=None):
        if not revision:
            branch = self.default_branch or self.fallback_branch
            revision = 'origin/%s' % branch

        code, out, err = self.run('git', 'checkout', '--force', revision)
        if code != 0:
            raise RepositoryError(
                RepositoryError.FAILED_TO_CHECKOUT.format(revision),
            )
        return [code, out, err]

    def clone(self):
        """Clones the repository."""
        cmd = ['git', 'clone', '--no-single-branch']

        if self.use_shallow_clone():
            cmd.extend(['--depth', str(self.repo_depth)])

        cmd.extend([self.repo_url, '.'])

        code, stdout, stderr = self.run(*cmd)
        if code != 0:
            raise RepositoryError

        self._get_repo_info()
        return code, stdout, stderr

    @property
    def tags(self):
        versions = []
        repo = self._get_repo_info()
        for tag in repo.tags:
            try:
                versions.append(
                    VCSVersion(self, str(tag['identifier']), tag['name']),
                )
            except ValueError:
                # ValueError: Cannot resolve commit as tag TAGNAME points to a
                # blob object - use the `.object` property instead to access it
                # This is not a real tag for us, so we skip it
                # https://github.com/rtfd/readthedocs.org/issues/4440
                log.warning('Git tag skipped: %s', tag, exc_info=True)
                continue
        return versions

    @property
    def branches(self):
        repo = self._get_repo_info()
        versions = [
            VCSVersion(self, branch['name'], branch['identifier'])
            for branch in repo.branches
        ]
        return versions

    @property
    def commit(self):
        return self._get_repo_info().commit

    @property
    def submodules(self):
        return self._get_repo_info().submodules

    def checkout(self, identifier=None):
        """Checkout to identifier or latest."""
        super().checkout()
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
                raise RepositoryError(
                    RepositoryError.INVALID_SUBMODULES.format(submodules),
                )

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

    @property
    def env(self):
        env = super().env
        env['GIT_DIR'] = os.path.join(self.working_dir, '.git')
        # Don't prompt for username, this requires Git 2.3+
        env['GIT_TERMINAL_PROMPT'] = '0'
        return env
