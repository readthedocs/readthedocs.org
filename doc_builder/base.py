import os

from projects.utils import run


class BaseBuilder(object):

    def _find_makefile(self, project):
        makes = [makefile for makefile in project.find('Makefile') if 'doc' in makefile]
        make_dir = makes[0].replace('/Makefile', '')
        return make_dir

    def _cd_makefile(self, project):
        os.chdir(self._find_makefile(project))

    def run_make_command(self, project, command, backup_command):
        try:
            self._cd_makefile(project)
            results = run(command)
            if results[0] != 0:
                raise OSError
        except (IndexError, OSError):
            os.chdir(project.path)
            results = run(backup_command)
        return results

    def reset(self, project):
        raise NotImplementedError

    def clean(self, project):
        raise NotImplementedError

    def build(self, project, version):
        raise NotImplementedError
