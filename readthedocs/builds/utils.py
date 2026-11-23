"""Utilities for the builds app."""

from contextlib import contextmanager
from time import monotonic

from django.core.cache import cache

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import GENERIC_EXTERNAL_VERSION_NAME
from readthedocs.builds.constants import GITHUB_EXTERNAL_VERSION_NAME
from readthedocs.builds.constants import GITLAB_EXTERNAL_VERSION_NAME
from readthedocs.projects.constants import BITBUCKET_REGEXS
from readthedocs.projects.constants import GITHUB_PULL_REQUEST_URL
from readthedocs.projects.constants import GITHUB_REGEXS
from readthedocs.projects.constants import GITLAB_MERGE_REQUEST_URL
from readthedocs.projects.constants import GITLAB_REGEXS


def get_github_username_repo(url):
    if "github" in url:
        for regex in GITHUB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if "bitbucket" in url:
        for regex in BITBUCKET_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_gitlab_username_repo(url=None):
    if "gitlab" in url:
        for regex in GITLAB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_vcs_url(*, project, version_type, version_name):
    """
    Generate VCS (github, gitlab, bitbucket) URL for this version.

    Example: https://github.com/rtfd/readthedocs.org/tree/3.4.2/.
    External version example: https://github.com/rtfd/readthedocs.org/pull/99/.
    """
    if version_type == EXTERNAL:
        if "github" in project.repo:
            user, repo = get_github_username_repo(project.repo)
            return GITHUB_PULL_REQUEST_URL.format(
                user=user,
                repo=repo,
                number=version_name,
            )
        if "gitlab" in project.repo:
            user, repo = get_gitlab_username_repo(project.repo)
            return GITLAB_MERGE_REQUEST_URL.format(
                user=user,
                repo=repo,
                number=version_name,
            )
        # TODO: Add VCS URL for Bitbucket.
        return ""

    url = ""
    if ("github" in project.repo) or ("gitlab" in project.repo):
        url = f"/tree/{version_name}/"
    elif "bitbucket" in project.repo:
        url = f"/src/{version_name}"

    # TODO: improve this replacing
    return project.repo.replace("git://", "https://").replace(".git", "") + url


def external_version_name(build_or_version):
    """Returns a string identifying the external build/version's nature."""
    if not build_or_version.is_external:
        return None

    project = build_or_version.project

    if project.is_github_project:
        return GITHUB_EXTERNAL_VERSION_NAME

    if project.is_gitlab_project:
        return GITLAB_EXTERNAL_VERSION_NAME

    # TODO: Add External Version Name for Bitbucket.
    return GENERIC_EXTERNAL_VERSION_NAME


@contextmanager
def memcache_lock(lock_id, lock_expire, app_identifier):
    """
    Create a lock using django's cache for running a celery task.

    From http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#cookbook-task-serial
    """
    timeout_at = monotonic() + lock_expire - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, app_identifier, lock_expire)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)


class RunTracker:
    """
    Run a job one at a time without losing requests made while it runs.

    A request made while the job is running can't start a second run,
    and the running one may have started too early to cover it.
    So the request is remembered, and the job runs once more when it finishes.

    Only for jobs that redo all their work on each run, like a version sync:
    one extra run then covers every request made during the previous one.

    The state is two cache keys:

    - ``running_key`` is set from ``start()`` until ``finish()``.
      It expires after ``expire`` seconds so a job that never finishes can't block new runs.
    - ``run_again_key`` is set when ``start()`` is called while the job is running.
    """

    def __init__(self, name, expire=60):
        self.running_key = f"run-tracker:{name}:running"
        self.run_again_key = f"run-tracker:{name}:run-again"
        self.expire = expire

    def start(self):
        """Return ``True`` if the caller should run the job now."""
        if cache.add(self.running_key, True, self.expire):
            return True
        cache.set(self.run_again_key, True, self.expire * 10)
        return False

    def finish(self):
        """Return ``True`` if the caller should run the job again."""
        cache.delete(self.running_key)
        run_again = cache.get(self.run_again_key, False)
        cache.delete(self.run_again_key)
        return run_again
