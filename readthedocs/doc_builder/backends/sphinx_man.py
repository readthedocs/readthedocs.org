from glob import glob
import os

from django.conf import settings

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as ManpageBuilder
from projects.utils import run
from core.utils import copy_file_to_app_servers


class Builder(ManpageBuilder):

    @restoring_chdir
    def build(self):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b man  -d _build/doctrees . _build/man' % project.venv_bin(
                version=self.version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b man . _build/man"
        build_results = run(build_command)
        return build_results

    def move(self):
        project = self.version.project
        outputted_path = os.path.join(project.conf_dir(self.version.slug),
                                    '_build', 'man')
        to_path = os.path.join(settings.MEDIA_ROOT,
                               'man',
                               project.slug,
                               self.version.slug)
        from_globs = glob(os.path.join(outputted_path, "*.1"))
        if from_globs:
            from_file = from_globs[0]
            to_file = os.path.join(to_path, '%s.1' % project.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_file_to_app_servers(from_file, to_file)
            else:
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                run('mv -f %s %s' % (from_file, to_file))
