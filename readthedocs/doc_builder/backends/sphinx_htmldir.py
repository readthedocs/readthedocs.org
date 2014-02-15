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
            build_command = '%s -b readthedocsdirhtml -D language=%s . _build/html' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocsdirhtml . _build/html" % project.language
        build_results = run(build_command)
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results
