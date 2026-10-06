"""Utilities for the builds app."""

import json
import re
from contextlib import contextmanager
from time import monotonic

import structlog
from django.conf import settings
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
from readthedocs.storage import build_commands_storage


log = structlog.get_logger(__name__)


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


def normalize_build_command(command, project_slug, version_slug):
    """
    Sanitize the build command to be shown to users.

    It removes internal variables and long paths to make them nicer.
    """
    docroot = settings.DOCROOT.rstrip("/")  # remove trailing '/'

    # Remove Docker hash from DOCROOT when running it locally
    # DOCROOT contains the Docker container hash (e.g. b7703d1b5854).
    # We have to remove it from the DOCROOT it self since it changes each time
    # we spin up a new Docker instance locally.
    container_hash = "/"
    if settings.RTD_DOCKER_COMPOSE:
        docroot = re.sub("/[0-9a-z]+/?$", "", settings.DOCROOT, count=1)
        container_hash = "/([0-9a-z]+/)?"

    regex = f"{docroot}{container_hash}{project_slug}/envs/{version_slug}(/bin/)?"
    command = re.sub(regex, "", command, count=1)

    # Remove explicit variable names we use to run commands,
    # since users don't care about these.
    regex = r"^\$READTHEDOCS_VIRTUALENV_PATH/bin/"
    command = re.sub(regex, "", command, count=1)

    regex = r"^\$CONDA_ENVS_PATH/\$CONDA_DEFAULT_ENV/bin/"
    command = re.sub(regex, "", command, count=1)
    return command


def get_build_commands_from_storage(build):
    """
    Return build commands from storage for ``cold_storage`` builds.

    Returns ``None`` when commands can't be loaded from storage and callers
    should keep using serializer output.
    """
    if not settings.RTD_SAVE_BUILD_COMMANDS_TO_STORAGE:
        return None

    if not build.cold_storage:
        return None

    storage_path = build.storage_path
    if not build_commands_storage.exists(storage_path):
        return None

    try:
        json_resp = build_commands_storage.open(storage_path).read()
        commands = json.loads(json_resp)
        for buildcommand in commands:
            buildcommand["command"] = normalize_build_command(
                buildcommand["command"],
                build.project.slug,
                build.get_version_slug(),
            )
        return commands
    except Exception:
        log.exception(
            "Failed to read build data from storage.",
            path=storage_path,
        )
        return None
