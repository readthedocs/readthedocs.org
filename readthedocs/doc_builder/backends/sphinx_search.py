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
            build_command = '%s -b json -D language=%s . _build/json' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -b json -D language=%s . _build/json" % project.language
        build_results = run(build_command)
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

    def upload(self, **kwargs):
        page_list = process_all_json_files(self.version)
        data = {
            'page_list': page_list,
            'version_pk': self.version.pk,
            'project_pk': self.version.project.pk
        }
        log_msg = ' '.join([page['path'] for page in page_list])
        log.info("(Search Index) Sending Data: %s [%s]" % (self.version.project.slug, log_msg))
        apiv2.index_search.post({'data': data})
