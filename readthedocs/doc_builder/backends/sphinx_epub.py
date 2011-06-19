import os
from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run

from django.conf import settings


class Builder(HtmlBuilder):

    @restoring_chdir
    def build(self, version):
        project = version.project
        os.chdir(project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b epub . _build/epub' % project.venv_bin(
                version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b epub . _build/epub"
        build_results = run(build_command)
        if build_results[0] == 0:
            os.chdir('_build/epub')
            to_path = os.path.join(settings.MEDIA_ROOT,
                                   'epub',
                                   project.slug,
                                   version.slug)
            if not os.path.exists(to_path):
                os.makedirs(to_path)
            from_file = os.path.join(os.getcwd(), "*.epub")
            to_file = os.path.join(to_path, "%s.epub" % project.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_to_app_servers('/'.join(
                        from_file.split('/')[0:-1]),
                                    '/'.join(to_file.split('/')[0:-1]))
            else:
                run('mv -f %s %s' % (from_file, to_file))
        else:
            print "Not copying epub file because of error"
        return build_results
