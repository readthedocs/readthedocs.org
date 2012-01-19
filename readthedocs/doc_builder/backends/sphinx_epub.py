import os
from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run
from core.utils import copy_file_to_app_servers


from django.conf import settings


class Builder(HtmlBuilder):

    @restoring_chdir
    def build(self):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b epub . _build/epub' % project.venv_bin(
                version=self.version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b epub . _build/epub"
        build_results = run(build_command)
        return build_results

    def move(self):
        project = self.version.project
        outputted_path = os.path.join(project.conf_dir(self.version.slug),
                                    '_build', 'epub')
        to_path = os.path.join(settings.MEDIA_ROOT,
                               'epub',
                               project.slug,
                               self.version.slug)
        from_file = os.path.join(outputted_path, "*.epub")
        to_file = os.path.join(to_path, "%s.epub" % project.slug)
        if getattr(settings, "MULTIPLE_APP_SERVERS", None):
            copy_file_to_app_servers(from_file, to_file)
        else:
            if not os.path.exists(to_path):
                os.makedirs(to_path)
            run('mv -f %s %s' % (from_file, to_file))
