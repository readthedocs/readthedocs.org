from glob import glob
import re
import os

from django.conf import settings

from doc_builder.base import BaseBuilder
from projects.utils import run
from projects.tasks import copy_to_app_servers

latex_re = re.compile('the LaTeX files are in (.*)\.')
pdf_re = re.compile('Output written on (.+) \(')


class Builder(BaseBuilder):

    def build(self, version):
        project = version.project
        os.chdir(project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            latex_results = run('%s -b latex -d _build/doctrees   . _build/latex' % project.venv_bin(version=version.slug, bin='sphinx-build'))
        else:
            latex_results = run('sphinx-build -b latex '
                            '-d _build/doctrees   . _build/latex')

        if latex_results[0] == 0:
            os.chdir('_build/latex')
            tex_globs = glob('*.tex')
            if tex_globs:
                tex_file = tex_globs[0]
            else:
                return False
            pdf_results = run('pdflatex -interaction=nonstopmode %s' % tex_file)
            pdf_match = pdf_re.search(pdf_results[1])
            if pdf_match:
                from_file = os.path.join(os.getcwd(),
                                         "%s" % pdf_match.group(1).strip())
                to_path = os.path.join(settings.MEDIA_ROOT,
                                       'pdf',
                                       project.slug,
                                       version.slug)
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                to_file = os.path.join(to_path, '%s.pdf' % project.slug)
                if os.path.exists(from_file):
                    if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                        copy_to_app_servers('/'.join(from_file.split('/')[0:-1]), '/'.join(to_file.split('/')[0:-1]))
                    else:
                        run('mv -f %s %s' % (from_file, to_file))
                else:
                    print "File doesn't exist, not symlinking."
            return True
        print "PDF Building failed. Moving on."
        return False
