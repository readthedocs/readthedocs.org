import os

from projects.utils import run


class BaseBuilder(object):

    def touch(self, project):
        print "Touching files"
        os.chdir(project.full_doc_path)
        os.system('touch * && touch */*')

    def clean(self, project):
        raise NotImplementedError

    def build(self, project, version):
        raise NotImplementedError
