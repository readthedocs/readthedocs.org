import logging
import shutil
import os

from django.conf import settings

from core.utils import copy_to_app_servers
from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run

from tastyapi import apiv2

log = logging.getLogger(__name__)


class Builder(HtmlBuilder):
    sphinx_builder = 'json'
    sphinx_build_dir = '_build/json'
    results_name = 'epub'
    type = 'sphinx_search'


    def __init__(self, version):
        self.version = version
        self.old_artifact_path = self.version.project.full_json_path(self.version.slug)

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
