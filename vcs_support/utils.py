from django.conf import settings
import os
import threading
import time

LOCK_ROOT = os.path.join(settings.SITE_ROOT, 'locks')
if not os.path.exists(LOCK_ROOT):
    os.mkdir(LOCK_ROOT)
        
        
def slug_from_wd(path):
    if path.endswith(os.path.sep):
        return os.path.basename(os.path.dirname(path))
    return os.path.basename(path)

class Lock(object):
    """
    A simple file based lock with timeout
    
    On entering the context, it will try to aquire the lock. If timeout passes,
    it just gets the lock anyway.
    
    If we're in the same thread as the one holding this lock, ignore the lock.
    """
    _thread_locals =  threading.local()
    _thread_locals.names = []
    
    def __init__(self, working_dir, timeout=5, polling_interval=0.1):
        self.name = slug_from_wd(working_dir)
        self.fpath = os.path.join(LOCK_ROOT, self.name)
        self.timeout = timeout
        self.polling_interval = polling_interval
        
    def __enter__(self):
        if self.name in Lock._thread_locals.names:
            print "Lock (%s): Locked by same thread" % self.name
            self.child = True
        else:
            self.child = False
            start = time.time()
            while os.path.exists(self.fpath):
                print "Lock (%s): Locked by other thread, waiting..." % self.name
                time.sleep(self.polling_interval)
                if time.time() - start > self.timeout:
                    print "Lock (%s): Force unlock, timeout reached" % self.name
                    os.remove(self.fpath)
                    break
            print "Lock (%s): Lock aquired" % self.name
            open(self.fpath, 'w').close()
            Lock._thread_locals.names.append(self.name)
        
    def __exit__(self, exc, value, tb):
        if self.child:
            print "Lock (%s): Not releasing, locked by same thread" % self.name
        else:
            print "Lock (%s): Releasing" % self.name
            os.remove(self.fpath)
            Lock._thread_locals.names.remove(self.name)

def locked_repo_method(meth):
    def _decorator(self, *args, **kwargs):
        with Lock(self.working_dir):
            return meth(self, *args, **kwargs)
    _decorator.__name__ = meth.__name__
    return _decorator