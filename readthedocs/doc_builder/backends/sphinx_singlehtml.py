import logging
import os

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run

log = logging.getLogger(__name__)


class Builder(HtmlBuilder):
    
    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b readthedocssinglehtml -D language=%s . _build/html' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocssinglehtml . _build/html" % project.language
        build_results = run(build_command)
        #self._zip_html()
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

class LocalMediaBuilder(HtmlBuilder):
    
    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b singlehtml -D language=%s . _build/html' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b singlehtml . _build/html" % project.language
        build_results = run(build_command)
        self._zip_html()
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results
