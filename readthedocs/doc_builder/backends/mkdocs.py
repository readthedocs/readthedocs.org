import os
import shutil
import codecs
import logging
import zipfile

from django.template import Template, Context
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from builds import utils as version_utils
from core.utils import copy_to_app_servers, copy_file_to_app_servers
from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from tastyapi import apiv2

log = logging.getLogger(__name__)

class Builder(BaseBuilder):
    """
    Mkdocs builder
    """

    def clean(self):
        pass

    def find_conf_file(self, project, version='latest'):
        if project.conf_py_file:
            log.debug('Inserting conf.py file path from model')
            return os.path.join(self.checkout_path(version), self.conf_py_file)
        files = project.find('mkdocs.yml', version)
        if not files:
            files = project.full_find('mkdocs.yml', version)
        if len(files) == 1:
            return files[0]
        elif len(files) > 1:
            for file in files:
                if file.find('doc', 70) != -1:
                    return file
        else:
            # Having this be translatable causes this odd error:
            # ProjectImportError(<django.utils.functional.__proxy__ object at 0x1090cded0>,)
            raise ProjectImportError(u"Conf File Missing. Please make sure you have a mkdocs.yml in your project.")

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.checkout_path(self.version.slug))
        if project.use_virtualenv:
            build_command = "%s build" % (
                project.venv_bin(version=self.version.slug,
                                 bin='mkdocs')
                )
        else:
            build_command = "mkdocs build"
        build_results = run(build_command, shell=True)
        return build_results

    def move(self, **kwargs):
        project = self.version.project
        build_path = os.path.join(project.checkout_path(self.version.slug), 'site')
        if os.path.exists(build_path):
            #Copy the html files.
            target = project.rtd_build_path(self.version.slug)
            if "_" in project.slug:
                new_slug = project.slug.replace('_', '-')
                new_target = target.replace(project.slug, new_slug)
                #Only replace 1, so user_builds doesn't get replaced >:x
                targets = [target, new_target]
            else:
                targets = [target]
            for target in targets:
                if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                    log.info("Copying docs to remote server.")
                    copy_to_app_servers(build_path, target)
                else:
                    if os.path.exists(target):
                        shutil.rmtree(target)
                    log.info("Copying docs on the local filesystem")
                    shutil.copytree(build_path, target)
        else:
            log.warning("Not moving docs, because the build dir is unknown.")
