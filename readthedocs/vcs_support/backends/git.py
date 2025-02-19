"""Git-related utilities."""

import re
from typing import Iterable

import structlog
from django.conf import settings

from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    LATEST_VERBOSE_NAME,
    STABLE_VERBOSE_NAME,
    TAG,
)
from readthedocs.config import ALL
from readthedocs.projects.constants import (
    GITHUB_PR_PULL_PATTERN,
    GITLAB_MR_PULL_PATTERN,
)
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion

log = structlog.get_logger(__name__)


class Backend(BaseVCS):

    """Git VCS backend."""

    fallback_branch = "master"  # default branch
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
        self.token = kwargs.get("token")
        self.repo_url = self._get_clone_url()

    def _get_clone_url(self):
        if "://" in self.repo_url:
            hacked_url = self.repo_url.split("://")[1]
            hacked_url = re.sub(".git$", "", hacked_url)
            clone_url = "https://%s" % hacked_url
            if self.token:
                clone_url = "https://{}@{}".format(self.token, hacked_url)
                return clone_url
            # Don't edit URL because all hosts aren't the same
            # else:
            #     clone_url = 'git://%s' % (hacked_url)
        return self.repo_url

    def update(self):
        """Clone and/or fetch remote repository."""
        super().update()

        self.clone()
        # TODO: We are still using return values in this function that are legacy.
        # This should be either explained or removed.
        return self.fetch()

    def get_remote_fetch_refspec(self):
        """
        Gets a valid remote reference for the identifier.

        See also: The <refspec> section from ``git help fetch``

        This method sits on top of a lot of legacy design.
        It decides how to treat the incoming ``Version.identifier`` from
        knowledge of how the caller (the build process) uses build data.
        Thi is:

        For branches:

        - Version.identifier is the branch name.
        - Version.verbose_name is also the branch name,
          except for latest and stable (machine created),
          where this is the alias name.

        For tags:

        - Version.identifier is the commit hash,
          except for latest, where this is the tag name.
        - Version.verbose_name is the tag name,
          except for latest and stable (machine created),
          where this is the alias name.

        For external versions:

        - Version.identifier is the commit hash.
        - Version.verbose_name is the PR number.

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
            if self.version_machine and self.verbose_name == STABLE_VERBOSE_NAME:
                if self.version_identifier:
                    return f"{self.version_identifier}"
                log.error("'stable' version without a commit hash.")
                return None

            tag_name = self.verbose_name
            # For a machine created "latest" tag, the name of the tag is set
            # in the `Version.identifier` field, note that it isn't a commit
            # hash, but the name of the tag.
            if self.version_machine and self.verbose_name == LATEST_VERBOSE_NAME:
                tag_name = self.version_identifier
            return f"refs/tags/{tag_name}:refs/tags/{tag_name}"

        if self.version_type == EXTERNAL:
            # Remote reference for Git providers where pull request builds are supported
            if self.project.is_github_project:
                return GITHUB_PR_PULL_PATTERN.format(id=self.verbose_name)
            if self.project.is_gitlab_project:
                return GITLAB_MR_PULL_PATTERN.format(id=self.verbose_name)

            log.warning(
                "Asked to do an external build for a Git provider that does not support "
                "fetching a pr/mr refspec.",
                project_slug=self.project.slug,
            )

    def clone(self):
        """Clones the repository."""
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
            message_id = RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED
            if settings.ALLOW_PRIVATE_REPOS:
                message_id = RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED
            raise RepositoryError(message_id=message_id) from exc

    def fetch(self):
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

    def get_available_submodules(self, config) -> tuple[bool, list]:
        """
        Returns the submodules available to use.

        .. note::

           Always call after `self.are_submodules_available`.

        Returns a tuple, the first element is a boolean indicating whether
        the submodules are available to use, the second element is a list
        of submodules paths, if the list is empty, it means that all
        submodules are available.

        The following cases are possible:

        - Include is `ALL`, returns `True` and `[]`.
        - Include is a list, returns `True` and the list of submodules.
        - Exclude is `ALL`, returns `False` and `[]`.
        - Exclude is a list, returns `True` and all available submodules
          but those from the list. If at the end there are no submodules
          left, returns `False` and the empty list.
        """
        if config.submodules.exclude == ALL:
            return False, []

        if config.submodules.exclude:
            submodules = list(self.submodules)
            for sub_path in config.submodules.exclude:
                path = sub_path.rstrip("/")
                try:
                    submodules.remove(path)
                except ValueError:
                    # TODO: Should we raise an error if the submodule is not found?
                    pass

            # If all submodules were excluded, we don't need to do anything.
            if not submodules:
                return False, []
            return True, submodules

        if config.submodules.include == ALL:
            return True, []

        if config.submodules.include:
            return True, config.submodules.include

        return False, []

    def checkout_revision(self, revision):
        try:
            code, out, err = self.run("git", "checkout", "--force", revision)
            return [code, out, err]
        except RepositoryError as exc:
            raise RepositoryError(
                message_id=RepositoryError.FAILED_TO_CHECKOUT,
                format_values={
                    "revision": revision,
                },
            ) from exc

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
            try:
                commit, ref = line.split(maxsplit=1)
            except ValueError:
                # Skip this line if we have a problem splitting the line
                continue
            if ref.startswith("refs/heads/"):
                branch = ref.replace("refs/heads/", "", 1)
                branches.append(VCSVersion(self, branch, branch))

            if ref.startswith("refs/tags/"):
                tag = ref.replace("refs/tags/", "", 1)
                # If the tag is annotated, then the real commit
                # will be on the ref ending with ^{}.
                if tag.endswith("^{}"):
                    light_tags[tag[:-3]] = commit
                else:
                    all_tags[tag] = commit

        # Merge both tags, lightweight tags will have
        # priority over annotated tags.
        all_tags.update(light_tags)
        tags = [VCSVersion(self, commit, tag) for tag, commit in all_tags.items()]

        return branches, tags

    @property
    def commit(self):
        _, stdout, _ = self.run("git", "rev-parse", "HEAD", record=False)
        return stdout.strip()

    @property
    def submodules(self) -> Iterable[str]:
        r"""
        Return an iterable of submodule paths in this repository.

        In order to get the submodules paths without initializing them,
        we parse the .gitmodules file. For this we make use of the
        ``git config --get-regexp`` command.

        Keys and values from the config can contain spaces.
        In order to parse the output unambiguously, we use the
        ``--null`` option to separate each result with a null character,
        and each key and value with a newline character.

        The command will produce an output like this:

        .. code-block:: text

           submodule.submodule-1.path\nsubmodule-1\0
           submodule.submodule-2.path\nsubmodule-2\0
           submodule.submodule-4.path\n\0

        .. note::

           - In the example each result is put in a new line for readability.
           - Isn't guaranteed that sub-keys will appear next to each other.
           - Isn't guaranteed that all submodules will have a path
             (they are probably invalid submodules).

        """
        exit_code, stdout, _ = self.run(
            "git",
            "config",
            "--null",
            "--file",
            ".gitmodules",
            "--get-regexp",
            # Get only the path key of each submodule.
            r"^submodule\..*\.path$",
            record=False,
        )
        if exit_code != 0:
            # The command fails if the project doesn't have submodules (the .gitmodules file doesn't exist).
            return []

        keys_and_values = stdout.split("\0")
        for key_and_value in keys_and_values:
            try:
                key, value = key_and_value.split("\n", maxsplit=1)
            except ValueError:
                # This should never happen, but we log a warning just in case
                # Git doesn't return the expected format.
                log.warning("Wrong key and value format.", key_and_value=key_and_value)
                continue

            if key.endswith(".path"):
                yield value
            else:
                # This should never happen, but we log a warning just in case the regex is wrong.
                log.warning("Unexpected key extracted fom .gitmodules.", key=key)

    def checkout(self, identifier=None):
        """Checkout to identifier or latest."""
        super().checkout()

        # NOTE: if there is no identifier, we default to default branch cloned
        if not identifier:
            return

        identifier = self.find_ref(identifier)
        # Checkout the correct identifier for this branch.
        code, out, err = self.checkout_revision(identifier)

        return code, out, err

    def update_submodules(self, config):
        # TODO: just rely on get_available_submodules when
        # not using a config file is fully deprecated.
        if self.are_submodules_available(config):
            valid, submodules = self.get_available_submodules(config)
            if valid:
                self.checkout_submodules(submodules, config.submodules.recursive)

    def checkout_submodules(self, submodules: list[str], recursive: bool):
        """
        Checkout all repository submodules.

        If submodules is empty, all submodules will be updated.
        """
        self.run("git", "submodule", "sync")
        cmd = [
            "git",
            "submodule",
            "update",
            "--init",
            "--force",
        ]
        if recursive:
            cmd.append("--recursive")
        cmd.append("--")
        cmd += submodules
        self.run(*cmd)

    def find_ref(self, ref):
        # If the ref already starts with 'origin/',
        # we don't need to do anything.
        if ref.startswith("origin/"):
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
