from functools import wraps
import os
import logging
import shutil

log = logging.getLogger(__name__)


def restoring_chdir(fn):
    #XXX:dc: This would be better off in a neutral module
    @wraps(fn)
    def decorator(*args, **kw):
        try:
            path = os.getcwd()
            return fn(*args, **kw)
        finally:
            os.chdir(path)
    return decorator


class BaseBuilder(object):
    """
    The Base for all Builders. Defines the API for subclasses.
    """

    def __init__(self, version, force=False):
        self.version = version
        self.force = force

    @restoring_chdir
    def force(self, **kwargs):
        """
        An optional step to force a build even when nothing has changed.
        """
        log.info("Forcing a build")
        self.force = True

    def build(self, id=None, **kwargs):
        """
        Do the actual building of the documentation.
        """
        raise NotImplementedError

    def move(self, **kwargs):
        """
        Move the documentation from it's generated place to its artifact directory.
        """
        target = self.version.project.artifact_path(version=self.version.slug, type=self.type)
        if os.path.exists(self.old_artifact_path):
            if os.path.exists(target):
                shutil.rmtree(target)
            log.info("Copying docs on the local filesystem")
            shutil.copytree(self.old_artifact_path, target)
        else:
            log.warning("Not moving docs, because the build dir is unknown.")

