import os

class BaseBuilder(object):

    def touch(self, version):
        print "Touching files"
        os.chdir(version.project.conf_dir(version.slug))
        os.system('touch * && touch */*')

    def clean(self, version):
        raise NotImplementedError

    def build(self, version):
        raise NotImplementedError
