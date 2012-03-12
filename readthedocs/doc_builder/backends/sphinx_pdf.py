from glob import glob
import re
import os
import logging

from django.conf import settings

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from core.utils import copy_file_to_app_servers


latex_re = re.compile('the LaTeX files are in (.*)\.')
pdf_re = re.compile('Output written on (.+) \(')

log = logging.getLogger(__name__)

class Builder(BaseBuilder):

    @restoring_chdir
    def build(self):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        #Default to this so we can return it always.
        pdf_results = (1, '', '')
        if project.use_virtualenv:
            latex_results = run('%s -b latex -d _build/doctrees   . _build/latex' %
                                project.venv_bin(version=self.version.slug, bin='sphinx-build'))
        else:
            latex_results = run('sphinx-build -b latex '
                            '-d _build/doctrees   . _build/latex')

        if latex_results[0] == 0:
            os.chdir('_build/latex')
            tex_globs = glob('*.tex')
            if tex_globs:
                tex_file = tex_globs[0]
                pdf_results = run('pdflatex -interaction=nonstopmode %s' % tex_file)
                pdf_match = pdf_re.search(pdf_results[1])
                if pdf_match:
                    to_path = os.path.join(settings.MEDIA_ROOT,
                           'pdf',
                           project.slug,
                           self.version.slug)
                    from_file = os.path.join(os.getcwd(), "*.pdf")
                    to_file = os.path.join(to_path, '%s.pdf' % project.slug)
                    if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                        copy_file_to_app_servers(from_file, to_file)
                    else:
                        if not os.path.exists(to_path):
                            os.makedirs(to_path)
                        run('mv -f %s %s' % (from_file, to_file))
        else:
            log.warning("PDF Building failed. Moving on.")
        return (latex_results, pdf_results)


    def move(self):
        #This needs to be thought about more because of all the state above.
        #We could just shove the filename on the instance or something.
        return True
