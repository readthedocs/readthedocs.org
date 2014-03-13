from glob import glob
import os
import logging

from django.conf import settings

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from core.utils import copy_file_to_app_servers


log = logging.getLogger(__name__)


class Builder(BaseBuilder):
    type = 'sphinx_pdf'

    def __init__(self, version):
        super(Builder).__init__(*args, **kwargs)
        self.old_artifact_path = self.version.project.full_latex_path(self.version.slug)

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        #Default to this so we can return it always.
        results = {}
        if project.use_virtualenv:
            results['latex'] = run('%s -b latex -D language=%s -d _build/doctrees . _build/latex'
                                % (project.venv_bin(version=self.version.slug,
                                                   bin='sphinx-build'), project.language))
        else:
            results['latex'] = run('sphinx-build -b latex -D language=%s -d _build/doctrees '
                                '. _build/latex' % project.language)

        if latex_results[0] == 0:
            os.chdir('_build/latex')
            tex_files = glob('*.tex')

            if tex_files:
                # Run LaTeX -> PDF conversions
                pdflatex_cmds = [('pdflatex -interaction=nonstopmode %s'
                                 % tex_file) for tex_file in tex_files]
                results['pdf'] = run(*pdflatex_cmds)
            else:
                results['pdf'] = (0, "No tex files found", "No tex files found")

        if results['latex'][0] != 0 or results['pdf'][0] != 0:
            log.warning("PDF Building failed.")
        return results
