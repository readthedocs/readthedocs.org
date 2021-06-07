"""Utilities for the builds app."""

import logging
from contextlib import contextmanager
from time import monotonic

import regex
from django.core.cache import cache

from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.constants import (
    BITBUCKET_REGEXS,
    GITHUB_PULL_REQUEST_URL,
    GITHUB_REGEXS,
    GITLAB_MERGE_REQUEST_URL,
    GITLAB_REGEXS,
)

log = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 180  # Lock expires in 3 hours


def get_github_username_repo(url):
    if 'github' in url:
        for pattern in GITHUB_REGEXS:
            match = pattern.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if 'bitbucket' in url:
        for pattern in BITBUCKET_REGEXS:
            match = pattern.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_gitlab_username_repo(url=None):
    if 'gitlab' in url:
        for pattern in GITLAB_REGEXS:
            match = pattern.search(url)
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
        if 'github' in project.repo:
            user, repo = get_github_username_repo(project.repo)
            return GITHUB_PULL_REQUEST_URL.format(
                user=user,
                repo=repo,
                number=version_name,
            )
        if 'gitlab' in project.repo:
            user, repo = get_gitlab_username_repo(project.repo)
            return GITLAB_MERGE_REQUEST_URL.format(
                user=user,
                repo=repo,
                number=version_name,
            )
        # TODO: Add VCS URL for BitBucket.
        return ''

    url = ''
    if ('github' in project.repo) or ('gitlab' in project.repo):
        url = f'/tree/{version_name}/'
    elif 'bitbucket' in project.repo:
        url = f'/src/{version_name}'

    # TODO: improve this replacing
    return project.repo.replace('git://', 'https://').replace('.git', '') + url


@contextmanager
def memcache_lock(lock_id, oid):
    """
    Create a lock using django's cache for running a celery task.

    From http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#cookbook-task-serial
    """
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else.
            cache.delete(lock_id)


def match_regex(pattern, text, timeout=1):
    """
    Find a match using regex.search.

    .. note::
       We use the regex module with the timeout arg to avoid ReDoS.
       We could use a finite state machine type of regex too,
       but there isn't a stable library at the time of writting this code.
    """
    try:
        match = regex.search(
            pattern,
            text,
            # Compatible with the re module
            flags=regex.VERSION0,
            timeout=timeout,
        )
        return match
    except TimeoutError:
        log.exception(
            'Timeout while parsing regex. pattern=%s, input=%s',
            pattern, text,
        )
    except Exception as e:
        log.exception('Error parsing regex: %s', e)
    return None
