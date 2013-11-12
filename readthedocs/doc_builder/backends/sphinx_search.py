import logging
import shutil
import os

from django.conf import settings

from core.utils import copy_to_app_servers
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

    def move(self, **kwargs):
        project = self.version.project
        if project.full_build_path(self.version.slug):
            #Copy the html files.
            to_path = os.path.join(settings.MEDIA_ROOT, 'json', project.slug,
                       self.version.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                log.info("Copying json to remote server.")
                copy_to_app_servers(
                    project.full_json_path(self.version.slug), to_path)
            else:
                if os.path.exists(to_path):
                    shutil.rmtree(to_path)
                log.info("Copying json on the local filesystem")
                shutil.copytree(
                    project.full_json_path(self.version.slug), to_path)
        else:
            log.warning("Not moving json, because the build dir is unknown.")