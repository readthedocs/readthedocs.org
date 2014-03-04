import logging
import os
import time
import stat

log = logging.getLogger(__name__)


class Lock(object):
    """
    A simple file based lock with timeout

    On entering the context, it will try to aquire the lock. If timeout passes,
    it just gets the lock anyway.

    If we're in the same thread as the one holding this lock, ignore the lock.
    """

    def __init__(self, project, version, timeout=5, polling_interval=0.1):
        self.name = project.slug
        self.fpath = os.path.join(project.doc_path), '%s__rtdlock' % version.slug)
        self.timeout = timeout
        self.polling_interval = polling_interval

    def __enter__(self):
        start = time.time()
        while os.path.exists(self.fpath):
            lock_age = time.time() - os.stat(self.fpath)[stat.ST_MTIME]
            if lock_age > self.timeout:
                log.info("Lock (%s): Force unlock, old lockfile" %
                         self.name)
                os.remove(self.fpath)
                break
            log.info("Lock (%s): Locked, waiting.." % self.name)
            time.sleep(self.polling_interval)
            timesince = time.time() - start
            if timesince > self.timeout:
                log.info("Lock (%s): Force unlock, timeout reached" %
                         self.name)
                os.remove(self.fpath)
                break
            log.info(("%s still locked after %.2f seconds; retry for %.2f"
                      " seconds") % (self.name, timesince, self.timeout))
        open(self.fpath, 'w').close()
        log.info("Lock (%s): Lock aquired" % self.name)

    def __exit__(self, exc, value, tb):
        try:
            log.info("Lock (%s): Releasing" % self.name)
            os.remove(self.fpath)
        except:
            log.error("Lock (%s): Failed to release, ignoring..." % self.name,
                      exc_info=True)
