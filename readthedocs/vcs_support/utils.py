# -*- coding: utf-8 -*-
"""Locking utilities."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import errno
import logging
import os
import stat
import time

from builtins import object

log = logging.getLogger(__name__)


class LockTimeout(Exception):
    pass


class Lock(object):

    """
    A simple file based lock with timeout.

    On entering the context, it will try to acquire the lock. If timeout passes,
    it just gets the lock anyway.

    If we're in the same thread as the one holding this lock, ignore the lock.
    """

    def __init__(self, project, version, timeout=5, polling_interval=0.1):
        self.name = project.slug
        self.fpath = os.path.join(
            project.doc_path, '%s__rtdlock' % version.slug)
        self.timeout = timeout
        self.polling_interval = polling_interval

    def __enter__(self):
        start = time.time()
        while os.path.exists(self.fpath):
            lock_age = time.time() - os.stat(self.fpath)[stat.ST_MTIME]
            if lock_age > self.timeout:
                log.info('Lock (%s): Force unlock, old lockfile', self.name)
                os.remove(self.fpath)
                break
            log.info('Lock (%s): Locked, waiting..', self.name)
            time.sleep(self.polling_interval)
            timesince = time.time() - start
            if timesince > self.timeout:
                log.info('Lock (%s): Force unlock, timeout reached', self.name)
                os.remove(self.fpath)
                break
            log.info(
                '%s still locked after %.2f seconds; retry for %.2f'
                ' seconds', self.name, timesince, self.timeout)
        open(self.fpath, 'w').close()
        log.info('Lock (%s): Lock acquired', self.name)

    def __exit__(self, exc, value, tb):
        try:
            log.info('Lock (%s): Releasing', self.name)
            os.remove(self.fpath)
        except OSError as e:
            # We want to ignore "No such file or directory" and log any other
            # type of error.
            if e.errno != errno.ENOENT:
                log.exception(
                    'Lock (%s): Failed to release, ignoring...',
                    self.name,
                )


class NonBlockingLock(object):

    """
    Acquire a lock in a non-blocking manner.

    Instead of waiting for a lock, depending on the lock file age, either
    acquire it immediately or throw LockTimeout

    :param project: Project being built
    :param version: Version to build
    :param max_lock_age: If file lock is older than this, forcibly acquire.
        None means never force
    """

    def __init__(self, project, version, max_lock_age=None):
        self.fpath = os.path.join(
            project.doc_path, '%s__rtdlock' % version.slug)
        self.max_lock_age = max_lock_age
        self.name = project.slug

    def __enter__(self):
        path_exists = os.path.exists(self.fpath)
        if path_exists and self.max_lock_age is not None:
            lock_age = time.time() - os.stat(self.fpath)[stat.ST_MTIME]
            if lock_age > self.max_lock_age:
                log.info('Lock (%s): Force unlock, old lockfile', self.name)
                os.remove(self.fpath)
            else:
                raise LockTimeout(
                    'Lock ({}): Lock still active'.format(self.name))
        elif path_exists:
            raise LockTimeout('Lock ({}): Lock still active'.format(self.name))
        open(self.fpath, 'w').close()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            log.info('Lock (%s): Releasing', self.name)
            os.remove(self.fpath)
        except (IOError, OSError) as e:
            # We want to ignore "No such file or directory" and log any other
            # type of error.
            if e.errno != errno.ENOENT:
                log.error(
                    'Lock (%s): Failed to release, ignoring...',
                    self.name,
                    exc_info=True,
                )
