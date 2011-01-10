import re
import os

from django.conf import settings

from doc_builder.base import BaseBuilder
from projects.utils import run

latex_re = re.compile('the LaTeX files are in (.*)\.')

class Builder(BaseBuilder):

    def build(self, project):
        self._cd_makefile(project)
        latex_results = run('make latex')
        match = latex_re.search(latex_results[1])
        if match:
            latex_dir = match.group(1).strip()
            os.chdir(latex_dir)
            pdf_results = run('make')
            #Check the return code was good before symlinking
            if pdf_results[0] == 0:
                from_path = os.path.join(os.getcwd(),
                                         "%s.pdf" % project.slug)
                to_path = os.path.join(settings.MEDIA_ROOT,
                                       'pdf',
                                       project.slug,
                                       'latest')
                os.makedirs(to_path)
                to_file = os.path.join(to_path, '%s.pdf' % project.slug)
                if os.path.exists(to_file):
                    run('ln -sf %s %s' % (from_path, to_file))
                else:
                    print "File doesn't exist, not symlinking."
            else:
                print "PDF Building failed. Moving on."
                if project.build_pdf:
                    project.build_pdf = False
                    project.save()
