"""Git-related utilities."""

import re
from typing import Iterable
from urllib.parse import urlparse

import structlog
from django.conf import settings

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import TAG
from readthedocs.config import ALL
from readthedocs.projects.constants import GITHUB_PR_PULL_PATTERN
from readthedocs.projects.constants import GITLAB_MR_PULL_PATTERN
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS
from readthedocs.vcs_support.base import VCSVersion


log = structlog.get_logger(__name__)


class Backend(BaseVCS):
    """Git VCS backend."""

    fallback_branch = "master"  # default branch
    repo_depth = 50

    def __init__(self, *args, use_token=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_token = use_token
        self.repo_url = self._get_clone_url()

    def _get_clone_url(self):
        if self.repo_url.startswith(("https://", "http://")) and self.use_token:
            parsed_url = urlparse(self.repo_url)
            return f"{parsed_url.scheme}://$READTHEDOCS_GIT_CLONE_TOKEN@{parsed_url.netloc}{parsed_url.path}"
        return self.repo_url

    def update(self):
        """Clone and/or fetch remote repository."""
        super().update()

        if self.project.git_checkout_command:
            # Run custom checkout step if defined
            if isinstance(self.project.git_checkout_command, list):
                for cmd in self.project.git_checkout_command:
                    # NOTE: we need to pass ``escape_command=False`` here to be
                    # able to expand environment variables.
                    code, stdout, stderr = self.run(*cmd.split(), escape_command=False)
                return

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
        # Here we point directly to the remote branch name and update our local remote
        # refspec to point here.
        # The original motivation for putting 'refs/remotes/origin/<branch>' as the local refspec
        # was an assumption in the .branches property that iterates over everything in
        # refs/remotes/origin. We might still keep this pattern as it seems to be the most solid
        # convention for storing a remote:local refspec mapping.
        branch_ref = "refs/heads/{branch}:refs/remotes/origin/{branch}"
        tag_ref = "refs/tags/{tag}:refs/tags/{tag}"

        if self.version.type == BRANCH:
            branch = self.version.verbose_name
            # For latest and stable, the identifier is the name of the branch.
            if self.version.machine:
                branch = self.version.identifier
                # If there is't an identifier, it can be the case for an initial build that started BEFORE
                # a webhook or sync versions task has concluded what the default branch is.
                if not branch:
                    log.error(
                        "Machine created version without a branch name.",
                        version_slug=self.version.slug,
                    )
                    return None
            return branch_ref.format(branch=branch)

        if self.version.type == TAG:
            tag = self.version.verbose_name
            if self.version.machine:
                # For stable, the identifier is the commit hash.
                # A "stable" tag is automatically created with Version.machine=True,
                # denoting that it's not a branch/tag that really exists.
                # Because we don't know if it originates from the default branch or some
                # other tagged release, we will fetch the exact commit it points to.
                if self.version.slug == STABLE:
                    if not self.version.identifier:
                        log.error("'stable' version without a commit hash.")
                    return self.version.identifier

                # For latest, the identifier is the tag name.
                tag = self.version.identifier

            return tag_ref.format(tag=tag)

        if self.version.type == EXTERNAL:
            # Remote reference for Git providers where pull request builds are supported
            if self.project.is_github_project:
                return GITHUB_PR_PULL_PATTERN.format(id=self.version.verbose_name)
            if self.project.is_gitlab_project:
                return GITLAB_MR_PULL_PATTERN.format(id=self.version.verbose_name)

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

    def has_ssh_key_with_write_access(self) -> bool:
        """
        Check if the SSH key has write access to the repository.

        This is done by trying to push to the repository in dry-run mode.

        We create a temporary remote to test the SSH key,
        since we need the remote to be in the SSH format,
        which isn't always the case for projects that are public,
        and changing the URL of the default remote may be a breaking
        change for some projects.

        .. note::

           This check is better done just after the clone step,
           to ensure that no commands controled by the user are run.
        """
        remote_name = "rtd-test-ssh-key"
        ssh_url = self.project.repo
        if ssh_url.startswith("http"):
            parsed_url = urlparse(ssh_url)
            ssh_url = f"git@{parsed_url.netloc}:{parsed_url.path.lstrip('/')}"

        try:
            cmd = ["git", "remote", "add", remote_name, ssh_url]
            self.run(*cmd, record=False)

            cmd = ["git", "push", "--dry-run", remote_name]
            code, stdout, stderr = self.run(*cmd, record=False, demux=True)

            if code == 0:
                return True

            # NOTE: if the command fails, it doesn't necessarily mean the key
            # doesn't have write access, there are a couple of other reasons
            # why this may fail, so we check for the error message.

            # This error is shown when the repo is archived, but the key has write access.
            if "ERROR: This repository was archived so it is read-only" in stderr:
                return True

            # This error is shown when the repo is empty, but we don't know if the key has write access or not.
            # We assume it has write access just to be safe, future steps will fail after the repo is cloned anyway.
            # Example: error: src refspec refs/heads/master does not match any
            pattern = r"error: src refspec refs/heads/\w does not match any"
            if re.search(pattern, stderr):
                return True

            # Example: ERROR: Permission to user/repo denied to deploy key
            pattern = r"ERROR: Permission to .* denied to deploy key"
            if re.search(pattern, stderr):
                return False

            errors_read_access_only = [
                "ERROR: The key you are authenticating with has been marked as read only",
                "ERROR: Write access to repository not granted",
                # This error is shown when the key isn't registered in GH at all.
                "git@github.com: Permission denied (publickey).",
                # We don't know if the key has write access or not,
                # but since the key can't be used from the builders,
                # it should be safe to return False.
                "ERROR: The repository owner has an IP allow list enabled",
                # Gitlab:
                "ERROR: This deploy key does not have write access to this project.",
                "remote: This deploy key does not have write access to this project.",
                # Bitbucket:
                "fatal: Could not read from remote repository.",
            ]
            for pattern in errors_read_access_only:
                if pattern in stderr:
                    return False

            # This is an error when the repo URL is not a git+ssh URL,
            # we don't know if the key has write access or not, as the URL is invalid.
            # Log and return False for now.
            if "fatal: could not read Username for" in stderr:
                log.error(
                    "Invalid repo URL for SSH key check.",
                    project_slug=self.project.slug,
                    repo_url=self.project.repo,
                    ssh_url=ssh_url,
                    exit_code=code,
                    stdout=stdout,
                    stderr=stderr,
                )
                return False

            # Log any other errors that we don't know about.
            log.error(
                "Unknown error when checking SSH key access.",
                project_slug=self.project.slug,
                exit_code=code,
                stdout=stdout,
                stderr=stderr,
            )
            return False
        finally:
            # Always remove the temporary remote.
            self.run("git", "remote", "remove", remote_name, record=False)

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
        # Skip adding a remote reference if we are building "latest",
        # and the user hasn't defined a default branch (which means we need to use the default branch from the repo).
        omit_remote_reference = self.version.is_machine_latest and not self.project.default_branch
        if not omit_remote_reference:
            remote_reference = self.get_remote_fetch_refspec()
            if remote_reference:
                # TODO: We are still fetching the latest 50 commits.
                # A PR might have another commit added after the build has started...
                cmd.append(remote_reference)

        # Log a warning, except for machine versions since it's a known bug that
        # we haven't stored a remote refspec in Version for those "stable" versions.
        # This could be the case for an unknown default branch.
        elif not self.version.machine:
            # We are doing a fetch without knowing the remote reference.
            # This is expensive, so log the event.
            log.warning(
                "Git fetch: Could not decide a remote reference for version. "
                "Is it an empty default branch?",
                project_slug=self.project.slug,
                verbose_name=self.version.verbose_name,
                version_type=self.version.type,
                version_identifier=self.version.identifier,
            )

        # TODO: Explain or remove the return value
        code, stdout, stderr = self.run(*cmd)
        return code, stdout, stderr

    def are_submodules_available(self, config):
        """Test whether git submodule checkout step should be performed."""
        submodules_in_config = config.submodules.exclude != ALL or config.submodules.include
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

    def get_default_branch(self):
        """
        Return the default branch of the repository.

        The default branch is the branch that is checked out when cloning the
        repository. This is usually master or main, it can be configured
        in the repository settings.

        The ``git symbolic-ref`` command will produce an output like:

        .. code-block:: text

           origin/main
        """
        cmd = ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
        _, stdout, _ = self.run(*cmd, demux=True, record=False)
        default_branch = stdout.strip().removeprefix("origin/")
        return default_branch

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
        exit_code, stdout, _ = self.run(*cmd, demux=True, record=False)

        if exit_code != 0:
            raise RepositoryError(message_id=RepositoryError.FAILED_TO_GET_VERSIONS)

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

        # Do not checkout anything else if the project has a custom Git checkout command.
        # The ``git checkout`` command has to be executed inside the ``update()`` method.
        if self.project.git_checkout_command:
            return

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


def parse_version_from_ref(ref: str):
    """
    Parse the version name and type from a Git ref.

    The ref can be a branch or a tag.

    :param ref: The ref to parse (e.g. refs/heads/main, refs/tags/v1.0.0).
    :returns: A tuple with the version name and type.
    """
    heads_prefix = "refs/heads/"
    tags_prefix = "refs/tags/"
    if ref.startswith(heads_prefix):
        return ref.removeprefix(heads_prefix), BRANCH
    if ref.startswith(tags_prefix):
        return ref.removeprefix(tags_prefix), TAG

    raise ValueError(f"Invalid ref: {ref}")
