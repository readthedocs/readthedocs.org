# -*- coding: utf-8 -*-

"""Locking utilities."""
import errno
import structlog
import os
import stat
import sys
import time


log = structlog.get_logger(__name__)


class LockTimeout(Exception):
    pass


class Lock:

    """
    A simple file based lock with timeout.

    On entering the context, it will try to acquire the lock. If timeout passes,
    it just gets the lock anyway.

    If we're in the same thread as the one holding this lock, ignore the lock.
    """

    def __init__(self, project, version, timeout=5, polling_interval=0.1):
        self.name = project.slug
        self.fpath = os.path.join(
            project.doc_path,
            '%s__rtdlock' % version.slug,
        )
        self.timeout = timeout
        self.polling_interval = polling_interval

    def __enter__(self):
        start = time.time()
        log.bind(
            project_slug=self.name,
        )
        while os.path.exists(self.fpath):
            lock_age = time.time() - os.stat(self.fpath)[stat.ST_MTIME]
            if lock_age > self.timeout:
                log.debug('Force unlock, old lockfile.')
                os.remove(self.fpath)
                break
            log.debug('Locked, waiting...')
            time.sleep(self.polling_interval)
            timesince = time.time() - start
            if timesince > self.timeout:
                log.debug('Force unlock, timeout reached')
                os.remove(self.fpath)
                break
            log.debug(
                'Lock still locked after some time. Retrying in some seconds',
                locked_time=timesince,
                seconds=self.timeout,
            )
        open(self.fpath, 'w').close()
        log.debug('Lock acquired.')

    def __exit__(self, exc, value, tb):
        log.bind(project_slug=self.name)

        try:
            log.debug('Releasing lock.')
            os.remove(self.fpath)
        except OSError as e:
            # We want to ignore "No such file or directory" and log any other
            # type of error.
            if e.errno != errno.ENOENT:
                log.exception('Failed to release, ignoring...')


class NonBlockingLock:

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
        self.base_path = project.doc_path
        self.fpath = os.path.join(
            self.base_path,
            f'{version.slug}__rtdlock',
        )
        self.max_lock_age = max_lock_age
        self.name = project.slug

    # TODO: migrate these to regular methods instead.
    # Alias to use them as functions
    def acquire_lock(self):
        return self.__enter__()

    def release_lock(self):
        return self.__exit__(*sys.exc_info())

    def __enter__(self):
        path_exists = os.path.exists(self.fpath)
        log.bind(project_slug=self.name)
        if path_exists and self.max_lock_age is not None:
            lock_age = time.time() - os.stat(self.fpath)[stat.ST_MTIME]
            if lock_age > self.max_lock_age:
                log.debug('Force unlock, old lockfile')
                os.remove(self.fpath)
            else:
                raise LockTimeout(
                    'Lock ({}): Lock still active'.format(self.name),
                )
        elif path_exists:
            raise LockTimeout('Lock ({}): Lock still active'.format(self.name),)
        # Create dirs if they don't exists
        os.makedirs(self.base_path, exist_ok=True)
        open(self.fpath, 'w').close()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.bind(project_slug=self.name)
        try:
            log.debug('Releasing lock.')
            os.remove(self.fpath)
        except (IOError, OSError) as e:
            # We want to ignore "No such file or directory" and log any other
            # type of error.
            if e.errno != errno.ENOENT:
                log.error(
                    'Failed to release, ignoring...',
                    exc_info=True,
                )
