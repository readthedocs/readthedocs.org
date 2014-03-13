import os
import shutil
import codecs
from glob import glob
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

class BaseSphinx(BaseBuilder):
    """
    The parent for most sphinx builders.
    """

    def __init__(self, *args, **kwargs):
        super(BaseSphinx, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(self.version.project.conf_dir(self.version.slug), self.sphinx_build_dir)

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        force_str = " -E " if self._force else ""
        if project.use_virtualenv:
            build_command = "%s %s -b %s -D language=%s . %s " % (
                project.venv_bin(version=self.version.slug,
                                 bin='sphinx-build'),
                force_str,
                self.sphinx_builder,
                project.language,
                self.sphinx_build_dir,
                )
        else:
            build_command = ("sphinx-build %s -b %s -D language=%s . %s"
                             % (
                                force_str, 
                                self.sphinx_builder,
                                project.language,
                                self.sphinx_build_dir,
                                )
                             )
        results = run(build_command, shell=True)
        return results



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


class HtmlBuilder(BaseSphinx):
    type = 'sphinx'
    sphinx_builder = 'readthedocs'
    sphinx_build_dir = '_build/html'


class HtmlDirBuilder(HtmlBuilder):
    type = 'sphinx_htmldir'
    sphinx_builder = 'readthedocsdirhtml'


class SingleHtmlBuilder(HtmlBuilder):
    type = 'sphinx_singlehtml'
    sphinx_builder = 'readthedocssinglehtml'


class SearchBuilder(BaseSphinx):
    type = 'sphinx_search'
    sphinx_builder = 'json'
    sphinx_build_dir = '_build/json'

    
class LocalMediaBuilder(BaseSphinx):
    type = 'sphinx_localmedia'
    sphinx_builder = 'readthedocssinglehtmllocalmedia'
    sphinx_build_dir = '_build/localmedia'

    @restoring_chdir
    def move(self, **kwargs):
        log.info("Creating zip file from %s" % self.old_artifact_path)
        target_file = os.path.join(self.target, '%s.zip' % self.version.project.slug)
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        if os.path.exists(target_file):
            os.remove(target_file)

        # Create a <slug>.zip file
        os.chdir(self.old_artifact_path)
        archive = zipfile.ZipFile(target_file, 'w')
        for root, subfolders, files in os.walk('.'):
            for file in files:
                to_write = os.path.join(root, file)
                archive.write(
                    filename=to_write,
                    arcname=os.path.join("%s-%s" % (self.version.project.slug,
                                                    self.version.slug),
                                         to_write)
                )
        archive.close()


class EpubBuilder(BaseSphinx):
    type = 'sphinx_epub'
    sphinx_builder = 'epub'
    sphinx_build_dir = '_build/epub'

    def move(self, **kwargs):
        from_globs = glob(os.path.join(self.old_artifact_path, "*.epub"))
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        if from_globs:
            from_file = from_globs[0]
            to_file = os.path.join(self.target, "%s.epub" % self.version.project.slug)
            run('mv -f %s %s' % (from_file, to_file))

class PdfBuilder(BaseBuilder):
    type = 'sphinx_pdf'
    sphinx_build_dir = '_build/latex'

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        #Default to this so we can return it always.
        results = {}
        if project.use_virtualenv:
            latex_results = run('%s -b latex -D language=%s -d _build/doctrees . _build/latex'
                                % (project.venv_bin(version=self.version.slug,
                                                   bin='sphinx-build'), project.language))
        else:
            latex_results = run('sphinx-build -b latex -D language=%s -d _build/doctrees '
                                '. _build/latex' % project.language)

        if latex_results[0] == 0:
            os.chdir('_build/latex')
            tex_files = glob('*.tex')

            if tex_files:
                # Run LaTeX -> PDF conversions
                pdflatex_cmds = [('pdflatex -interaction=nonstopmode %s'
                                 % tex_file) for tex_file in tex_files]
                pdf_results = run(*pdflatex_cmds)
            else:
                pdf_results = (0, "No tex files found", "No tex files found")

            results = [
                latex_results[0] + pdf_results[0],
                latex_results[1] + pdf_results[1],
                latex_results[2] + pdf_results[2],
            ]
        else:
            results = latex_results
        return results

    def move(self, **kwargs):
        from_globs = glob(os.path.join(self.old_artifact_path, "*.pdf"))
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        if from_globs:
            from_file = from_globs[0]
            to_file = os.path.join(self.target, "%s.pdf" % self.version.project.slug)
            run('mv -f %s %s' % (from_file, to_file))

