import logging
import os

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run
from search.parse_json import process_all_json_files
from tastyapi import apiv2

log = logging.getLogger(__name__)


class Builder(HtmlBuilder):

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b json . _build/json' % project.venv_bin(
                version=self.version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b json . _build/json"
        build_results = run(build_command)
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

    def upload(self, **kwargs):
        data = {
            'page_list': process_all_json_files(self.version),
            'version_pk': self.version.pk,
            'project_pk': self.version.project.pk
        }
        apiv2.index_search.post({'data': data})
