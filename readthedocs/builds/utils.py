"""Utilities for the builds app."""

from contextlib import contextmanager

from celery.five import monotonic
from django.core.cache import cache

from readthedocs.projects.constants import (
    BITBUCKET_REGEXS,
    GITHUB_REGEXS,
    GITLAB_REGEXS,
)

LOCK_EXPIRE = 60 * 180  # Lock expires in 3 hours


def get_github_username_repo(url):
    if 'github' in url:
        for regex in GITHUB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if 'bitbucket' in url:
        for regex in BITBUCKET_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_gitlab_username_repo(url=None):
    if 'gitlab' in url:
        for regex in GITLAB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


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
