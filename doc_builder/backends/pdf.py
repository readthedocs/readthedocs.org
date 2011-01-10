from glob import glob
import re
import os

from django.conf import settings

from doc_builder.base import BaseBuilder
from projects.utils import run

latex_re = re.compile('the LaTeX files are in (.*)\.')
pdf_re = re.compile('Output written on (.+) \(')


class Builder(BaseBuilder):

    def build(self, project, version):
        version_slug = 'latest'
        if version:
            version_slug = version.slug
        os.chdir(project.conf_filename.rstrip('conf.py'))
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
                from_file = os.path.join(os.getcwd(),
                                         "%s" % pdf_match.group(1).strip())
                to_path = os.path.join(settings.MEDIA_ROOT,
                                       'pdf',
                                       project.slug,
                                       version_slug)
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                to_file = os.path.join(to_path, '%s.pdf' % project.slug)
                if os.path.exists(from_file):
                    run('mv -f %s %s' % (from_file, to_file))
                else:
                    print "File doesn't exist, not symlinking."
            return True
        print "PDF Building failed. Moving on."
        if project.build_pdf:
            project.build_pdf = False
            project.save()
        return False
