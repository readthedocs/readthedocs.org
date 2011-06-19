import os


def restoring_chdir(fn):
    def decorator(*args, **kw):
        try:
            path = os.getcwd()
            return fn(*args, **kw)
        finally:
            os.chdir(path)
    return decorator


class BaseBuilder(object):

    @restoring_chdir
    def touch(self, version):
        print "Touching files"
        os.chdir(version.project.conf_dir(version.slug))
        os.system('touch * && touch */*')

    def clean(self, version):
        raise NotImplementedError

    def build(self, version):
        raise NotImplementedError
