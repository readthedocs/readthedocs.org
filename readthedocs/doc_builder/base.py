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
    """
    The Base for all Builders. Defines the API for subclasses.
    """

    @restoring_chdir
    def force(self, version):
        """
        An optional step to force a build even when nothing has changed.
        """
        print "Forcing a build by touching files"
        os.chdir(version.project.conf_dir(version.slug))
        os.system('touch * && touch */*')

    def clean(self, version):
        """
        Clean up the version so it's ready for usage.

        This is used to add RTD specific stuff to Sphinx, and to
        implement whitelists on projects as well.

        It is guaranteed to be called before your project is built.
        """
        raise NotImplementedError

    def build(self, version):
        """
        Do the actual building of the documentation.
        """
        raise NotImplementedError

    def move(self, version):
        """
        Move the documentation from it's generated place to its final home.

        This needs to understand both a single server dev environment,
        as well as a multi-server environment.
        """
        raise NotImplementedError
