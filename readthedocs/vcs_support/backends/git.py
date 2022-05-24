"""Git-related utilities."""

import re

import git
import structlog
from django.core.exceptions import ValidationError
from git.exc import BadName, InvalidGitRepositoryError, NoSuchPathError
from gitdb.util import hex_to_bin

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

log = structlog.get_logger(__name__)


class Backend(BaseVCS):

    """Git VCS backend."""

    supports_tags = True
    supports_branches = True
    supports_submodules = True
    supports_lsremote = True
    fallback_branch = 'master'  # default branch
    repo_depth = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = kwargs.get('token')
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
            self._repo
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False
        return True

    @property
    def _repo(self):
        """Get a `git.Repo` instance from the current `self.working_dir`."""
        return git.Repo(self.working_dir, expand_vars=False)

    def are_submodules_available(self, config):
        """Test whether git submodule checkout step should be performed."""
        submodules_in_config = (
            config.submodules.exclude != ALL or config.submodules.include
        )
        if not submodules_in_config:
            return False

        # Keep compatibility with previous projects
        return bool(self.submodules)

    def validate_submodules(self, config):
        """
        Returns the submodules and check that its URLs are valid.

        .. note::

           Always call after `self.are_submodules_available`.

        :returns: tuple(bool, list)

        Returns `True` if all required submodules URLs are valid.
        Returns a list of all required submodules:
        - Include is `ALL`, returns all submodules available.
        - Include is a list, returns just those.
        - Exclude is `ALL` - this should never happen.
        - Exclude is a list, returns all available submodules
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
        return code, stdout, stderr

    def checkout_revision(self, revision=None):
        if not revision:
            branch = self.default_branch or self.fallback_branch
            revision = 'origin/%s' % branch

        try:
            code, out, err = self.run('git', 'checkout', '--force', revision)
            return [code, out, err]
        except RepositoryError:
            raise RepositoryError(
                RepositoryError.FAILED_TO_CHECKOUT.format(revision),
            )

    def clone(self):
        """Clones the repository."""
        cmd = ['git', 'clone', '--no-single-branch']

        if self.use_shallow_clone():
            cmd.extend(['--depth', str(self.repo_depth)])

        cmd.extend([self.repo_url, '.'])

        try:
            code, stdout, stderr = self.run(*cmd)
            return code, stdout, stderr
        except RepositoryError:
            raise RepositoryError(RepositoryError.CLONE_ERROR())

    def lsremote(self, include_tags=True, include_branches=True):
        """
        Use ``git ls-remote`` to list branches and tags without cloning the repository.

        :returns: tuple containing a list of branch and tags
        """
        if not include_tags and not include_branches:
            return [], []

        extra_args = []
        if include_tags:
            extra_args.append("--tags")
        if include_branches:
            extra_args.append("--heads")

        cmd = ["git", "ls-remote", *extra_args, self.repo_url]

        self.check_working_dir()
        _, stdout, _ = self.run(*cmd, demux=True, record=False)

        branches = []
        # Git has two types of tags: lightweight and annotated.
        # Lightweight tags are the "normal" ones.
        all_tags = {}
        light_tags = {}
        for line in stdout.splitlines():
            commit, ref = line.split()
            if ref.startswith("refs/heads/"):
                branch = ref.replace("refs/heads/", "", 1)
                branches.append(VCSVersion(self, branch, branch))

            if ref.startswith("refs/tags/"):
                tag = ref.replace("refs/tags/", "", 1)
                # If the tag is annotated, then the real commit
                # will be on the ref ending with ^{}.
                if tag.endswith('^{}'):
                    light_tags[tag[:-3]] = commit
                else:
                    all_tags[tag] = commit

        # Merge both tags, lightweight tags will have
        # priority over annotated tags.
        all_tags.update(light_tags)
        tags = [VCSVersion(self, commit, tag) for tag, commit in all_tags.items()]

        return branches, tags

    @property
    def tags(self):
        versions = []
        repo = self._repo

        # Build a cache of tag -> commit
        # GitPython is not very optimized for reading large numbers of tags
        ref_cache = {}  # 'ref/tags/<tag>' -> hexsha
        # This code is the same that is executed for each tag in gitpython,
        # we execute it only once for all tags.
        for hexsha, ref in git.TagReference._iter_packed_refs(repo):
            gitobject = git.Object.new_from_sha(repo, hex_to_bin(hexsha))
            if gitobject.type == 'commit':
                ref_cache[ref] = str(gitobject)
            elif gitobject.type == 'tag' and gitobject.object.type == 'commit':
                ref_cache[ref] = str(gitobject.object)

        for tag in repo.tags:
            if tag.path in ref_cache:
                hexsha = ref_cache[tag.path]
            else:
                try:
                    hexsha = str(tag.commit)
                except ValueError:
                    # ValueError: Cannot resolve commit as tag TAGNAME points to a
                    # blob object - use the `.object` property instead to access it
                    # This is not a real tag for us, so we skip it
                    # https://github.com/rtfd/readthedocs.org/issues/4440
                    log.warning('Git tag skipped.', tag=tag, exc_info=True)
                    continue

            versions.append(VCSVersion(self, hexsha, str(tag)))
        return versions

    @property
    def branches(self):
        repo = self._repo
        versions = []
        branches = []

        # ``repo.remotes.origin.refs`` returns remote branches
        if repo.remotes:
            branches += repo.remotes.origin.refs

        for branch in branches:
            verbose_name = branch.name
            if verbose_name.startswith("origin/"):
                verbose_name = verbose_name.replace("origin/", "", 1)
            if verbose_name == "HEAD":
                continue
            versions.append(
                VCSVersion(
                    repository=self,
                    identifier=verbose_name,
                    verbose_name=verbose_name,
                )
            )
        return versions

    @property
    def commit(self):
        if self.repo_exists():
            _, stdout, _ = self.run('git', 'rev-parse', 'HEAD', record=False)
            return stdout.strip()
        return None

    @property
    def submodules(self):
        return list(self._repo.submodules)

    def checkout(self, identifier=None):
        """Checkout to identifier or latest."""
        super().checkout()
        # Find proper identifier
        if not identifier:
            identifier = self.default_branch or self.fallback_branch

        identifier = self.find_ref(identifier)

        # Checkout the correct identifier for this branch.
        code, out, err = self.checkout_revision(identifier)

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
            if self._repo.commit(ref):
                return True
        except (BadName, ValueError):
            return False
        return False
