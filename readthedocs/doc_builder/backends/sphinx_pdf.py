from glob import glob
import os
import logging

from django.conf import settings

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from core.utils import copy_file_to_app_servers


log = logging.getLogger(__name__)

class Builder(BaseBuilder):

    @restoring_chdir
    def build(self, **kwargs):
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
            if project.whitelisted:
                # For whitelisted projects, read LaTeX sources from conf.py
                conf_py_file = project.conf_file(self.version.slug)
                conf = {}
                execfile(conf_py_file, conf, conf)
                tex_files = [d[1] for d in conf.get('latex_documents', [])]
            else:
                # Otherwise treat all .tex files as sources
                tex_files = glob('*.tex')

            # Run LaTeX -> PDF conversions
            pdflatex_cmds = ['pdflatex -interaction=nonstopmode %s' % tex_file
                             for tex_file in tex_files]
            pdf_results = run(*pdflatex_cmds)

            if pdf_results[0] == 0:
                for tex_file in tex_files:
                    to_path = os.path.join(settings.MEDIA_ROOT,
                           'pdf',
                           project.slug,
                           self.version.slug)
                    to_file = os.path.join(to_path, '%s.pdf' % project.slug)
                    # pdflatex names its output predictably: foo.tex -> foo.pdf
                    pdf_filename = os.path.splitext(tex_file)[0] + '.pdf'
                    from_file = os.path.join(os.getcwd(), pdf_filename)
                    if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                        copy_file_to_app_servers(from_file, to_file)
                    else:
                        if not os.path.exists(to_path):
                            os.makedirs(to_path)
                        run('mv -f %s %s' % (from_file, to_file))

        if latex_results[0] != 0 or pdf_results[0] != 0:
            log.warning("PDF Building failed. Moving on.")
        return (latex_results, pdf_results)


    def move(self, **kwargs):
        #This needs to be thought about more because of all the state above.
        #We could just shove the filename on the instance or something.
        return True
