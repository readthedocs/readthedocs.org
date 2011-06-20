import os
import shutil

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.tasks import copy_to_app_servers
from projects.utils import run

from django.conf import settings

class Builder(HtmlBuilder):

    @restoring_chdir
    def build(self, version):
        project = version.project
        os.chdir(version.project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b dirhtml . _build/html' % project.venv_bin(
                version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b dirhtml . _build/html"
        build_results = run(build_command)
        return build_results

    def move(self, version):
        project = version.project
        if project.full_build_path(version.slug):
            target = project.rtd_build_path(version.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                print "Copying docs to remote server."
                copy_to_app_servers(project.full_build_path(version.slug), target)
            else:
                if os.path.exists(target):
                    shutil.rmtree(target)
                print "Copying docs on the local filesystem"
                shutil.copytree(project.full_build_path(version.slug), target)
        else:
            print "Not moving docs, because the build dir is unknown."
