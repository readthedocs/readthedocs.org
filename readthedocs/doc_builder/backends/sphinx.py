import os
import shutil
import codecs
import logging
import zipfile

from django.template import Template, Context, loader as template_loader
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from builds import utils as version_utils
from core.utils import copy_to_app_servers, copy_file_to_app_servers
from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from tastyapi import apiv2

log = logging.getLogger(__name__)

TEMPLATE_DIR = '%s/readthedocs/templates/sphinx' % settings.SITE_ROOT
STATIC_DIR = '%s/_static' % TEMPLATE_DIR

class Builder(BaseBuilder):
    """
    The parent for most sphinx builders.

    Also handles the default sphinx output of html.
    """

    def __init__(self, version):
        self.version = version
        self.old_artifact_path = self.version.project.full_build_path(self.version.slug)
        self.type = 'sphinx'

    def append_conf(self, **kwargs):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        """
        project = self.version.project
        #Open file for appending.
        outfile = codecs.open(project.conf_file(self.version.slug),
                              encoding='utf-8', mode='a')
        outfile.write("\n")
        conf_py_path = version_utils.get_conf_py_path(self.version)
        remote_version = version_utils.get_vcs_version_slug(self.version)
        github_info = version_utils.get_github_username_repo(self.version)
        bitbucket_info = version_utils.get_bitbucket_username_repo(self.version)
        if github_info[0] is None:
            display_github = False
        else:
            display_github = True
        if bitbucket_info[0] is None:
            display_bitbucket = False
        else:
            display_bitbucket = True

        rtd_ctx = Context({
            'versions': project.api_versions(),
            'downloads': self.version.get_downloads(pretty=True),
            'current_version': self.version.slug,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
            'conf_py_path': conf_py_path,
            'downloads': apiv2.version(self.version.pk).downloads.get()['downloads'],
            'api_host': getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org'),
            # GitHub
            'github_user': github_info[0],
            'github_repo': github_info[1],
            'github_version':  remote_version,
            'display_github': display_github,
            # BitBucket
            'bitbucket_user': bitbucket_info[0],
            'bitbucket_repo': bitbucket_info[1],
            'bitbucket_version':  remote_version,
            'display_bitbucket': display_bitbucket,
        })
        rtd_string = template_loader.get_template('doc_builder/conf.py.tmpl').render(rtd_ctx)
        outfile.write(rtd_string)

    @restoring_chdir
    def build(self, **kwargs):
        self.append_conf()
        project = self.version.project
        results = {}
        os.chdir(project.conf_dir(self.version.slug))
        force_str = " -E " if self.force else ""
        if project.use_virtualenv:
            build_command = "%s %s -b readthedocs -D language=%s . _build/html " % (
                project.venv_bin(version=self.version.slug,
                                 bin='sphinx-build'),
                force_str,
                project.language)
        else:
            build_command = ("sphinx-build %s -b readthedocs -D language=%s . _build/html"
                             % (force_str, project.language))
        results['html'] = run(build_command, shell=True)
        return results
