"""Git-related utilities."""

import re
from dataclasses import dataclass
from typing import Iterable

import git
import structlog
from django.core.exceptions import ValidationError
from gitdb.util import hex_to_bin

from readthedocs.builds.constants import BRANCH, EXTERNAL, TAG
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


@dataclass(slots=True)
class GitSubmodule:
    path: str
    url: str


class Backend(BaseVCS):

    """Git VCS backend."""

    supports_tags = True
    supports_branches = True
    supports_submodules = True
    supports_lsremote = True
    fallback_branch = 'master'  # default branch
    repo_depth = 50

    def __init__(self, *args, **kwargs):
        # The version_identifier is a Version.identifier value passed from the build process.
        # It has a special meaning since it's unfortunately not consistent, you need to be aware of
        # exactly how and where to use this.
        # See more in the .get_remote_fetch_refspec() docstring
        self.version_identifier = kwargs.pop("version_identifier")
        # We also need to know about Version.machine
        self.version_machine = kwargs.pop("version_machine")
        super().__init__(*args, **kwargs)
        self.token = kwargs.get('token')
        self.repo_url = self._get_clone_url()

        # While cloning, we can decide that we are not going to fetch anything
        self._skip_fetch = False

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

    # TODO: Remove when removing GIT_CLONE_FETCH_CHECKOUT_PATTERN
    def set_remote_url(self, url):
        return self.run('git', 'remote', 'set-url', 'origin', url)

    def update(self):
        """Clone and/or fetch remote repository."""
        super().update()
        from readthedocs.projects.models import Feature

        if self.project.has_feature(Feature.GIT_CLONE_FETCH_CHECKOUT_PATTERN):
            # New behavior: Clone is responsible for calling .repo_exists() and
            # .make_clean_working_dir()
            self.clone_ng()

            # TODO: We are still using return values in this function that are legacy.
            # This should be either explained or removed.
            return self.fetch_ng()

        # Old behavior
        if self.repo_exists():
            self.set_remote_url(self.repo_url)
            return self.fetch()
        self.make_clean_working_dir()
        # A fetch is always required to get external versions properly
        if self.version_type == EXTERNAL:
            self.clone()
            return self.fetch()
        return self.clone()

    def get_remote_fetch_refspec(self):
        """
        Gets a valid remote reference for the identifier.

        See also: The <refspec> section from ``git help fetch``

        This method sits on top of a lot of legacy design.
        It decides how to treat the incoming ``Version.identifier`` from
        knowledge of how the caller (the build process) uses build data.

        Version.identifier = a branch name (branches)
        Version.identifier = commit (tags)
        Version.identifier = commit (external versions)
        Version.verbose_name = branch alias, e.g. latest (branches)
        Version.verbose_name = tag name (tags)
        Version.verbose_name = PR number (external versions)

        :return: A refspec valid for fetch operation
        """

        if not self.version_type:
            log.warning(
                "Trying to resolve a remote reference without setting version_type is not "
                "possible",
                project_slug=self.project.slug,
            )
            return None

        # Branches have the branch identifier set by the caller who instantiated the
        # Git backend.
        # If version_identifier is empty, then the fetch operation cannot know what to fetch
        # and will fetch everything, in order to build what might be defined elsewhere
        # as the "default branch". This can be the case for an initial build started BEFORE
        # a webhook or sync versions task has concluded what the default branch is.
        if self.version_type == BRANCH and self.version_identifier:
            # Here we point directly to the remote branch name and update our local remote
            # refspec to point here.
            # The original motivation for putting 'refs/remotes/origin/<branch>' as the local refspec
            # was an assumption in the .branches property that iterates over everything in
            # refs/remotes/origin. We might still keep this pattern as it seems to be the most solid
            # convention for storing a remote:local refspec mapping.
            return (
                f"refs/heads/{self.version_identifier}:refs/remotes/origin/"
                f"{self.version_identifier}"
            )
        # Tags
        if self.version_type == TAG and self.verbose_name:
            # A "stable" tag is automatically created with Version.machine=True,
            # denoting that it's not a branch/tag that really exists.
            # Because we don't know if it originates from the default branch or some
            # other tagged release, we will fetch the exact commit it points to.
            if self.version_machine and self.verbose_name == "stable":
                if self.version_identifier:
                    return f"{self.version_identifier}"
                log.error("'stable' version without a commit hash.")
                return None
            return f"refs/tags/{self.verbose_name}:refs/tags/{self.verbose_name}"

        if self.version_type == EXTERNAL:
            # TODO: We should be able to resolve this without looking up in oauth registry
            git_provider_name = self.project.git_provider_name

            # Remote reference for Git providers where pull request builds are supported
            if git_provider_name == GITHUB_BRAND:
                return GITHUB_PR_PULL_PATTERN.format(id=self.verbose_name)
            if self.project.git_provider_name == GITLAB_BRAND:
                return GITLAB_MR_PULL_PATTERN.format(id=self.verbose_name)

            log.warning(
                "Asked to do an external build for a Git provider that does not support "
                "fetching a pr/mr refspec.",
                project_slug=self.project.slug,
            )

    def clone_ng(self):
        """
        Performs the next-generation (ng) git clone operation.

        This method is used when GIT_CLONE_FETCH_CHECKOUT_PATTERN is on.
        """
        # TODO: This seems to be legacy that can be removed.
        #  If the repository is already cloned, we don't do anything.
        #  It seems to originate from when a cloned repository was cached on disk,
        #  and so we can call call .update() several times in the same build.
        if self.repo_exists():
            return

        # TODO: This seems to be legacy that can be removed.
        #  There shouldn't be cases where we are asked to
        #  clone the repo in a non-clean working directory.
        #  The prior call to repo_exists() will return if a repo already exist with
        #  unclear guarantees about whether that even needs to be a fully consistent clone.
        self.make_clean_working_dir()

        # TODO: We should add "--no-checkout" in all git clone operations, except:
        #  There exists a case of version_type=BRANCH without a branch name.
        #  This case is relevant for building projects for the first time without knowing the name
        #  of the default branch. Once this case has been made redundant, we can have
        #  --no-checkout for all clones.
        # --depth 1: Shallow clone, fetch as little data as possible.
        cmd = ["git", "clone", "--depth", "1", self.repo_url, "."]

        try:
            # TODO: Explain or remove the return value
            code, stdout, stderr = self.run(*cmd)
            return code, stdout, stderr
        except RepositoryError as exc:
            raise RepositoryError(RepositoryError.CLONE_ERROR()) from exc

    def fetch_ng(self):
        """
        Performs the next-generation (ng) git fetch operation.

        This method is used when GIT_CLONE_FETCH_CHECKOUT_PATTERN is on.
        """

        # When git clone does NOT add --no-checkout, it's because we are going
        # to use the remote HEAD, so we don't have to fetch nor check out.
        if self._skip_fetch:
            log.info(
                "Skipping git fetch",
                version_identifier=self.version_identifier,
                version_machine=self.version_machine,
                version_verbose_name=self.verbose_name,
                version_type=self.version_type,
            )
            return

        # --force: Likely legacy, it seems to be irrelevant to this usage
        # --prune: Likely legacy, we don't expect a previous fetch command to have run
        # --prune-tags: Likely legacy, we don't expect a previous fetch command to have run
        # --depth: To keep backward compatibility for now.
        #          This flag should be made unnecessary, it's downloading commit data that's
        #          never used.
        cmd = [
            "git",
            "fetch",
            "origin",
            "--force",
            "--prune",
            "--prune-tags",
            "--depth",
            str(self.repo_depth),
        ]
        remote_reference = self.get_remote_fetch_refspec()

        if remote_reference:
            # TODO: We are still fetching the latest 50 commits.
            # A PR might have another commit added after the build has started...
            cmd.append(remote_reference)

        # Log a warning, except for machine versions since it's a known bug that
        # we haven't stored a remote refspec in Version for those "stable" versions.
        # This could be the case for an unknown default branch.
        elif not self.version_machine:
            # We are doing a fetch without knowing the remote reference.
            # This is expensive, so log the event.
            log.warning(
                "Git fetch: Could not decide a remote reference for version. "
                "Is it an empty default branch?",
                project_slug=self.project.slug,
                verbose_name=self.verbose_name,
                version_type=self.version_type,
                version_identifier=self.version_identifier,
            )

        # TODO: Explain or remove the return value
        code, stdout, stderr = self.run(*cmd)
        return code, stdout, stderr

    def repo_exists(self):
        """Test if the current working directory is a top-level git repository."""
        # If we are at the top-level of a git repository,
        # ``--show-prefix`` will return an empty string.
        exit_code, stdout, _ = self.run(
            "git", "rev-parse", "--show-prefix", record=False
        )
        return exit_code == 0 and stdout.strip() == ""

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
        # TODO: remove when all projects are required
        # to have a config file.
        return any(self.submodules)

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
            # TODO: Should we raise an error if the submodule is not found?
            if path in submodules:
                del submodules[path]

        if config.submodules.include != ALL and config.submodules.include:
            submodules_include = {}
            for sub_path in config.submodules.include:
                path = sub_path.rstrip('/')
                # TODO: Should we raise an error if the submodule is not found?
                if path in submodules:
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

    @staticmethod
    def _is_trigger_integration_gitlab(project):
        # If there is only one integration associated with the project, we
        # can unambiguously conclude that the external build was triggered by
        # a merge request.
        #
        # https://github.com/readthedocs/readthedocs.org/issues/9464

        # To avoid error like the following, the value corresponding to
        # Integration.GITLAB_WEBHOOK is hardcoded.
        #
        #   ImportError: cannot import name 'Project' from partially initialized module
        #   'readthedocs.projects.models' (most likely due to a circular import)
        _gitlab_webhook = "gitlab_webhook"  # Integration.GITLAB_WEBHOOK

        if (
            project.integrations.count() == 1
            and project.integrations.first().integration_type == _gitlab_webhook
        ):
            return True
        return False

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

            if (
                self.project.git_provider_name == GITLAB_BRAND
                or self._is_trigger_integration_gitlab(self.project)
            ):
                cmd.append(GITLAB_MR_PULL_PATTERN.format(id=self.verbose_name))

        code, stdout, stderr = self.run(*cmd)
        return code, stdout, stderr

    def checkout_revision(self, revision):
        try:
            code, out, err = self.run('git', 'checkout', '--force', revision)
            return [code, out, err]
        except RepositoryError as exc:
            raise RepositoryError(
                RepositoryError.FAILED_TO_CHECKOUT.format(revision),
            ) from exc

    def clone(self):
        """Clones the repository."""
        cmd = ['git', 'clone', '--no-single-branch']

        if self.use_shallow_clone():
            cmd.extend(['--depth', str(self.repo_depth)])

        cmd.extend([self.repo_url, '.'])

        try:
            code, stdout, stderr = self.run(*cmd)

            # TODO: for those VCS providers that don't tell us the `default_branch`
            # of the repository in the incoming webhook,
            # we need to get it from the cloned repository itself.
            #
            # cmd = ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD']
            # _, default_branch, _ = self.run(*cmd)
            # default_branch = default_branch.replace('refs/remotes/origin/', '')
            #
            # The idea is to hit the APIv2 here to update the `latest` version with
            # the `default_branch` we just got from the repository itself,
            # after clonning it.
            # However, we don't know the PK for the version we want to update.
            #
            # api_v2.version(pk).patch(
            #     {'default_branch': default_branch}
            # )

            return code, stdout, stderr
        except RepositoryError as exc:
            raise RepositoryError(RepositoryError.CLONE_ERROR()) from exc

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
            commit, ref = line.split(maxsplit=1)
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
    def submodules(self) -> Iterable[GitSubmodule]:
        r"""
        Return an iterable of submodules in this repository.

        In order to get the submodules URLs and paths without initializing them,
        we parse the .gitmodules file. For this we make use of the
        ``git config --get-regexp`` command.

        Keys and values from the config can contain spaces.
        In order to parse the output unambiguously, we use the
        ``--null`` option to separate each result with a null character,
        and each key and value with a newline character.

        The command will produce an output like this:

        .. code-block:: text

           submodule.submodule-1.url\nhttps://github.com/\0
           submodule.submodule-1.path\nsubmodule-1\0
           submodule.submodule-2.path\nsubmodule-2\0
           submodule.submodule-2.url\nhttps://github.com/\0
           submodule.submodule-3.url\nhttps://github.com/\0
           submodule.submodule-4.path\n\0

        .. note::

           - In the example each result is put in a new line for readability.
           - Isn't guaranteed that the url and path keys will appear next to each other.
           - Isn't guaranteed that all submodules will have a url and path.

        """
        exit_code, stdout, _ = self.run(
            "git",
            "config",
            "--null",
            "--file",
            ".gitmodules",
            "--get-regexp",
            # Get only the URL and path keys of each submodule.
            r"^submodule\..*\.(url|path)$",
            record=False,
        )
        if exit_code != 0:
            # The command fails if the project doesn't have submodules (the .gitmodules file doesn't exist).
            return []

        # Group the URLs and paths by submodule name/key.
        submodules = {}
        keys_and_values = stdout.split("\0")
        for key_and_value in keys_and_values:
            try:
                key, value = key_and_value.split("\n", maxsplit=1)
            except ValueError:
                # This should never happen, but we log a warning just in case
                # Git doesn't return the expected format.
                log.warning("Wrong key and value format.", key_and_value=key_and_value)
                continue

            if key.endswith(".url"):
                key = key.removesuffix(".url")
                submodules.setdefault(key, {})["url"] = value
            elif key.endswith(".path"):
                key = key.removesuffix(".path")
                submodules.setdefault(key, {})["path"] = value
            else:
                # This should never happen, but we log a warning just in case the regex is wrong.
                log.warning("Unexpected key extracted fom .gitmodules.", key=key)

        for submodule in submodules.values():
            # If the submodule doesn't have a URL or path, we skip it,
            # since it's not a valid submodule.
            url = submodule.get("url")
            path = submodule.get("path")
            if not url or not path:
                log.warning(
                    "Invalid submodule.", submoduel_url=url, submodule_path=path
                )
                continue
            # Return a generator to speed up when checking if the project has at least one submodule (e.g. ``any(self.submodules)``)
            yield GitSubmodule(
                url=url,
                path=path,
            )

    def checkout(self, identifier=None):
        """Checkout to identifier or latest."""
        super().checkout()

        # NOTE: if there is no identifier, we default to default branch cloned
        if not identifier:
            return

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
        # If the repository has no submodules, we don't need to do anything.
        # Otherwise, all submodules will be updated.
        if not submodules:
            return
        self.run('git', 'submodule', 'sync')
        cmd = [
            'git',
            'submodule',
            'update',
            '--init',
            '--force',
        ]
        if config.submodules.recursive:
            cmd.append("--recursive")
        cmd.append("--")
        cmd += submodules
        self.run(*cmd)

    def find_ref(self, ref):
        # If the ref already starts with 'origin/',
        # we don't need to do anything.
        if ref.startswith('origin/'):
            return ref

        # Check if ref is a branch of the origin remote
        if self.ref_exists("refs/remotes/origin/" + ref):
            return "origin/" + ref

        return ref

    def ref_exists(self, ref):
        exit_code, _, _ = self.run(
            "git", "show-ref", "--verify", "--quiet", "--", ref, record=False
        )
        return exit_code == 0
