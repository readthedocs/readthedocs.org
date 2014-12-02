import re
import os
import codecs
from glob import glob
import logging
import zipfile

from django.template import Context, loader as template_loader
from django.template.loader import render_to_string
from django.conf import settings

from builds import utils as version_utils
from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run, safe_write
from projects.exceptions import ProjectImportError
from tastyapi import apiv2

log = logging.getLogger(__name__)

TEMPLATE_DIR = '%s/readthedocs/templates/sphinx' % settings.SITE_ROOT
STATIC_DIR = '%s/_static' % TEMPLATE_DIR
PDF_RE = re.compile('Output written on (.*?)')


class BaseSphinx(BaseBuilder):

    """
    The parent for most sphinx builders.
    """

    def __init__(self, *args, **kwargs):
        super(BaseSphinx, self).__init__(*args, **kwargs)
        try:
            self.old_artifact_path = os.path.join(self.version.project.conf_dir(self.version.slug), self.sphinx_build_dir)
        except ProjectImportError:
            docs_dir = self.docs_dir()
            self.old_artifact_path = os.path.join(docs_dir, self.sphinx_build_dir)

    def _write_config(self):
        """
        Create ``conf.py`` if it doesn't exist.
        """
        docs_dir = self.docs_dir()
        conf_template = render_to_string('sphinx/conf.py.conf',
                                         {'project': self.version.project,
                                          'version': self.version,
                                          'template_dir': TEMPLATE_DIR,
                                          })
        conf_file = os.path.join(docs_dir, 'conf.py')
        safe_write(conf_file, conf_template)

    def append_conf(self, **kwargs):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        """

        # Pull config data
        try:
            conf_py_path = version_utils.get_conf_py_path(self.version)
        except ProjectImportError:
            self._write_config()
            self.create_index(extension='rst')

        project = self.version.project
        # Open file for appending.
        outfile = codecs.open(project.conf_file(self.version.slug), encoding='utf-8', mode='a')
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
            'current_version': self.version.slug,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
            'conf_py_path': conf_py_path,
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
            'commit': self.version.project.vcs_repo(self.version.slug).commit,
        })

        # Avoid hitting database and API if using Docker build environment
        if getattr(settings, 'DONT_HIT_API', False):
            rtd_ctx['versions'] = project.active_versions()
            rtd_ctx['downloads'] = self.version.get_downloads(pretty=True)
        else:
            rtd_ctx['versions'] = project.api_versions()
            rtd_ctx['downloads'] = (apiv2.version(self.version.pk)
                                    .downloads.get()['downloads'])

        rtd_string = template_loader.get_template('doc_builder/conf.py.tmpl').render(rtd_ctx)
        outfile.write(rtd_string)

    @restoring_chdir
    def build(self, **kwargs):
        self.clean()
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        force_str = " -E " if self._force else ""
        build_command = "%s -O %s -T %s -b %s -D language=%s . %s " % (
            project.venv_bin(version='latest',
                             bin='python'),
            project.venv_bin(version=self.version.slug,
                             bin='sphinx-build'),
            force_str,
            self.sphinx_builder,
            project.language,
            self.sphinx_build_dir,
        )
        results = run(build_command, shell=True)
        return results


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


class PdfBuilder(BaseSphinx):
    type = 'sphinx_pdf'
    sphinx_build_dir = '_build/latex'
    pdf_file_name = None

    @restoring_chdir
    def build(self, **kwargs):
        self.clean()
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        # Default to this so we can return it always.
        results = {}
        latex_results = run('%s -O %s -b latex -D language=%s -d _build/doctrees . _build/latex'
                            % (project.venv_bin(version='latest',
                                                bin='python'),
                               project.venv_bin(version=self.version.slug,
                                                bin='sphinx-build'),
                               project.language))

        if latex_results[0] == 0:
            os.chdir('_build/latex')
            tex_files = glob('*.tex')

            if tex_files:
                # Run LaTeX -> PDF conversions
                pdflatex_cmds = [('pdflatex -interaction=nonstopmode %s'
                                  % tex_file) for tex_file in tex_files]
                makeindex_cmds = [('makeindex -s python.ist %s.idx'
                                   % os.path.splitext(tex_file)[0]) for tex_file in tex_files]
                pdf_results = run(*pdflatex_cmds)
                ind_results = run(*makeindex_cmds)
                pdf_results = run(*pdflatex_cmds)
            else:
                pdf_results = (0, "No tex files found", "No tex files found")
                ind_results = (0, "No tex files found", "No tex files found")

            results = [
                latex_results[0] + ind_results[0] + pdf_results[0],
                latex_results[1] + ind_results[1] + pdf_results[1],
                latex_results[2] + ind_results[2] + pdf_results[2],
            ]
            pdf_match = PDF_RE.search(results[1])
            if pdf_match:
                self.pdf_file_name = pdf_match.group(1).strip()
        else:
            results = latex_results
        return results

    def move(self, **kwargs):
        if not os.path.exists(self.target):
            os.makedirs(self.target)

        exact = os.path.join(self.old_artifact_path, "%s.pdf" % self.version.project.slug)
        exact_upper = os.path.join(self.old_artifact_path, "%s.pdf" % self.version.project.slug.capitalize())

        if self.pdf_file_name and os.path.exists(self.pdf_file_name):
            from_file = self.pdf_file_name
        if os.path.exists(exact):
            from_file = exact
        elif os.path.exists(exact_upper):
            from_file = exact_upper
        else:
            from_globs = glob(os.path.join(self.old_artifact_path, "*.pdf"))
            if from_globs:
                from_file = from_globs[0]
            else:
                from_file = None
        if from_file:
            to_file = os.path.join(self.target, "%s.pdf" % self.version.project.slug)
            run('mv -f %s %s' % (from_file, to_file))
