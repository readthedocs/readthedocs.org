import os

from django.conf import settings

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as ManpageBuilder
from projects.tasks import copy_file_to_app_servers
from projects.utils import run


class Builder(ManpageBuilder):

    @restoring_chdir
    def build(self, version):
        project = version.project
        os.chdir(version.project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b man  -d _build/doctrees . _build/man' % project.venv_bin(
                version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b man . _build/man"
        build_results = run(build_command)
        if build_results[0] == 0:
            os.chdir('_build/man')
            to_path = os.path.join(settings.MEDIA_ROOT,
                                   'man',
                                   project.slug,
                                   version.slug)
            from_file = os.path.join(os.getcwd(), "*.1")
            to_file = os.path.join(to_path, '%s.1' % project.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_file_to_app_servers(from_file, to_file)
            else:
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                run('mv -f %s %s' % (from_file, to_file))
        else:
            print "Build error on man page"
        return build_results
