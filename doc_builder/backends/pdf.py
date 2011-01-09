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
                run('ln -sf %s.pdf %s/%s.pdf' % (os.path.join(os.getcwd(), project.slug),
                                        settings.MEDIA_ROOT,
                                        project.slug
                                       ))
            else:
                print "PDF Building failed. Moving on."
                #project.skip_sphinx = True
                #project.save()
