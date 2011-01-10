from django.conf import settings
import os
import time
import traceback

LOCK_ROOT = os.path.join(settings.SITE_ROOT, 'locks')
if not os.path.exists(LOCK_ROOT):
    os.mkdir(LOCK_ROOT)
        

class Lock(object):
    """
    A simple file based lock with timeout
    
    On entering the context, it will try to aquire the lock. If timeout passes,
    it just gets the lock anyway.
    
    If we're in the same thread as the one holding this lock, ignore the lock.
    """
    
    def __init__(self, slug, timeout=5, polling_interval=0.1):
        self.slug = slug
        self.fpath = os.path.join(LOCK_ROOT, self.name)
        self.timeout = timeout
        self.polling_interval = polling_interval
        
    def __enter__(self):
        start = time.time()
        while os.path.exists(self.fpath):
            print "Lock (%s): Locked, waiting.." % self.name
            time.sleep(self.polling_interval)
            timesince = time.time() - start
            if timesince > self.timeout:
                print "Lock (%s): Force unlock, timeout reached" % self.name
                os.remove(self.fpath)
                break
            print (
                "Lock (%s): Still locked after %.2f seconds, waiting for a max "
                "of %.2f seconds" % (self.name, timesince, self.timeout)
            )
        print "Lock (%s): Lock aquired" % self.name
        open(self.fpath, 'w').close()
        
    def __exit__(self, exc, value, tb):
        try:
            print "Lock (%s): Releasing" % self.name
            os.remove(self.fpath)
        except:
            traceback.print_exc()
            print "Lock (%s): Failed to release, ignoring..." % self.name