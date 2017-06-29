"""Sphinx_ backend for building docs.

.. _Sphinx: http://www.sphinx-doc.org/

"""
from __future__ import absolute_import
import os
import sys
import codecs
from glob import glob
import logging
import zipfile

from django.template import loader as template_loader
from django.template.loader import render_to_string
from django.conf import settings

from readthedocs.builds import utils as version_utils
from readthedocs.projects.utils import safe_write
from readthedocs.projects.exceptions import ProjectImportError
from readthedocs.restapi.client import api

from ..base import BaseBuilder, restoring_chdir
from ..exceptions import BuildEnvironmentError
from ..environments import DockerBuildCommand, BuildCommand
from ..constants import SPHINX_TEMPLATE_DIR, SPHINX_STATIC_DIR, PDF_RE
import six

log = logging.getLogger(__name__)


class BaseSphinx(BaseBuilder):

    """The parent for most sphinx builders."""

    def __init__(self, *args, **kwargs):
        super(BaseSphinx, self).__init__(*args, **kwargs)
        try:
            self.old_artifact_path = os.path.join(
                self.project.conf_dir(self.version.slug),
                self.sphinx_build_dir)
        except ProjectImportError:
            docs_dir = self.docs_dir()
            self.old_artifact_path = os.path.join(docs_dir, self.sphinx_build_dir)

    def _write_config(self, master_doc='index'):
        """Create ``conf.py`` if it doesn't exist."""
        docs_dir = self.docs_dir()
        conf_template = render_to_string('sphinx/conf.py.conf',
                                         {'project': self.project,
                                          'version': self.version,
                                          'template_dir': SPHINX_TEMPLATE_DIR,
                                          'master_doc': master_doc,
                                          })
        conf_file = os.path.join(docs_dir, 'conf.py')
        safe_write(conf_file, conf_template)

    def get_config_params(self):
        """Get configuration parameters to be rendered into the conf file."""
        # TODO this should be handled better in the theme
        conf_py_path = os.path.join(os.path.sep,
                                    self.version.get_conf_py_path(),
                                    '')
        remote_version = self.version.commit_name

        github_user, github_repo = version_utils.get_github_username_repo(
            url=self.project.repo)
        github_version_is_editable = (self.version.type == 'branch')
        display_github = github_user is not None

        bitbucket_user, bitbucket_repo = version_utils.get_bitbucket_username_repo(
            url=self.project.repo)
        bitbucket_version_is_editable = (self.version.type == 'branch')
        display_bitbucket = bitbucket_user is not None

        # Avoid hitting database and API if using Docker build environment
        if getattr(settings, 'DONT_HIT_API', False):
            versions = self.project.active_versions()
            downloads = self.version.get_downloads(pretty=True)
        else:
            versions = self.project.api_versions()
            downloads = api.version(self.version.pk).get()['downloads']

        return {
            'current_version': self.version.verbose_name,
            'project': self.project,
            'settings': settings,
            'static_path': SPHINX_STATIC_DIR,
            'template_path': SPHINX_TEMPLATE_DIR,
            'conf_py_path': conf_py_path,
            'api_host': getattr(settings, 'PUBLIC_API_URL', 'https://readthedocs.org'),
            'commit': self.project.vcs_repo(self.version.slug).commit,
            'versions': versions,
            'downloads': downloads,

            # GitHub
            'github_user': github_user,
            'github_repo': github_repo,
            'github_version': remote_version,
            'github_version_is_editable': github_version_is_editable,
            'display_github': display_github,

            # BitBucket
            'bitbucket_user': bitbucket_user,
            'bitbucket_repo': bitbucket_repo,
            'bitbucket_version': remote_version,
            'bitbucket_version_is_editable': bitbucket_version_is_editable,
            'display_bitbucket': display_bitbucket,
        }

    def append_conf(self, **__):
        """Modify given ``conf.py`` file from a whitelisted user's project."""
        try:
            self.version.get_conf_py_path()
        except ProjectImportError:
            master_doc = self.create_index(extension='rst')
            self._write_config(master_doc=master_doc)

        try:
            outfile_path = self.project.conf_file(self.version.slug)
            outfile = codecs.open(outfile_path, encoding='utf-8', mode='a')
        except (ProjectImportError, IOError):
            trace = sys.exc_info()[2]
            six.reraise(ProjectImportError('Conf file not found'), None, trace)

        # Append config to project conf file
        tmpl = template_loader.get_template('doc_builder/conf.py.tmpl')
        rendered = tmpl.render(self.get_config_params())

        with outfile:
            outfile.write("\n")
            outfile.write(rendered)

        # Print the contents of conf.py in order to make the rendered
        # configfile visible in the build logs
        self.run(
            'cat', os.path.relpath(outfile_path,
                                   self.project.checkout_path(self.version.slug)),
            cwd=self.project.checkout_path(self.version.slug),
        )

    def build(self):
        self.clean()
        project = self.project
        build_command = [
            'python',
            self.python_env.venv_bin(filename='sphinx-build'),
            '-T'
        ]
        if self._force:
            build_command.append('-E')
        build_command.extend([
            '-b', self.sphinx_builder,
            '-d', '_build/doctrees-{format}'.format(format=self.sphinx_builder),
            '-D', 'language={lang}'.format(lang=project.language),
            '.',
            self.sphinx_build_dir
        ])
        cmd_ret = self.run(
            *build_command,
            cwd=project.conf_dir(self.version.slug),
            bin_path=self.python_env.venv_bin()
        )
        return cmd_ret.successful


class HtmlBuilder(BaseSphinx):
    type = 'sphinx'
    sphinx_build_dir = '_build/html'

    def __init__(self, *args, **kwargs):
        super(HtmlBuilder, self).__init__(*args, **kwargs)
        if self.project.allow_comments:
            self.sphinx_builder = 'readthedocs-comments'
        else:
            self.sphinx_builder = 'readthedocs'


class HtmlDirBuilder(HtmlBuilder):
    type = 'sphinx_htmldir'

    def __init__(self, *args, **kwargs):
        super(HtmlDirBuilder, self).__init__(*args, **kwargs)
        if self.project.allow_comments:
            self.sphinx_builder = 'readthedocsdirhtml-comments'
        else:
            self.sphinx_builder = 'readthedocsdirhtml'


class SingleHtmlBuilder(HtmlBuilder):
    type = 'sphinx_singlehtml'

    def __init__(self, *args, **kwargs):
        super(SingleHtmlBuilder, self).__init__(*args, **kwargs)
        self.sphinx_builder = 'readthedocssinglehtml'


class SearchBuilder(BaseSphinx):
    type = 'sphinx_search'
    sphinx_builder = 'json'
    sphinx_build_dir = '_build/json'


class LocalMediaBuilder(BaseSphinx):
    type = 'sphinx_localmedia'
    sphinx_builder = 'readthedocssinglehtmllocalmedia'
    sphinx_build_dir = '_build/localmedia'

    @restoring_chdir
    def move(self, **__):
        log.info("Creating zip file from %s", self.old_artifact_path)
        target_file = os.path.join(self.target, '%s.zip' % self.project.slug)
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        if os.path.exists(target_file):
            os.remove(target_file)

        # Create a <slug>.zip file
        os.chdir(self.old_artifact_path)
        archive = zipfile.ZipFile(target_file, 'w')
        for root, __, files in os.walk('.'):
            for fname in files:
                to_write = os.path.join(root, fname)
                archive.write(
                    filename=to_write,
                    arcname=os.path.join("%s-%s" % (self.project.slug,
                                                    self.version.slug),
                                         to_write)
                )
        archive.close()


class EpubBuilder(BaseSphinx):
    type = 'sphinx_epub'
    sphinx_builder = 'epub'
    sphinx_build_dir = '_build/epub'

    def move(self, **__):
        from_globs = glob(os.path.join(self.old_artifact_path, "*.epub"))
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        if from_globs:
            from_file = from_globs[0]
            to_file = os.path.join(self.target, "%s.epub" % self.project.slug)
            self.run('mv', '-f', from_file, to_file)


class LatexBuildCommand(BuildCommand):

    """Ignore LaTeX exit code if there was file output"""

    def run(self):
        super(LatexBuildCommand, self).run()
        # Force LaTeX exit code to be a little more optimistic. If LaTeX
        # reports an output file, let's just assume we're fine.
        if PDF_RE.search(self.output):
            self.exit_code = 0


class DockerLatexBuildCommand(DockerBuildCommand):

    """Ignore LaTeX exit code if there was file output"""

    def run(self):
        super(DockerLatexBuildCommand, self).run()
        # Force LaTeX exit code to be a little more optimistic. If LaTeX
        # reports an output file, let's just assume we're fine.
        if PDF_RE.search(self.output):
            self.exit_code = 0


class PdfBuilder(BaseSphinx):

    """Builder to generate PDF documentation."""

    type = 'sphinx_pdf'
    sphinx_build_dir = '_build/latex'
    pdf_file_name = None

    def build(self):
        self.clean()
        cwd = self.project.conf_dir(self.version.slug)

        # Default to this so we can return it always.
        self.run(
            'python',
            self.python_env.venv_bin(filename='sphinx-build'),
            '-b', 'latex',
            '-D', 'language={lang}'.format(lang=self.project.language),
            '-d', '_build/doctrees',
            '.',
            '_build/latex',
            cwd=cwd,
            bin_path=self.python_env.venv_bin()
        )
        latex_cwd = os.path.join(cwd, '_build', 'latex')
        tex_files = glob(os.path.join(latex_cwd, '*.tex'))

        if not tex_files:
            raise BuildEnvironmentError('No TeX files were found')

        # Run LaTeX -> PDF conversions
        pdflatex_cmds = [
            ['pdflatex',
                '-interaction=nonstopmode',
                tex_file]
            for tex_file in tex_files]
        makeindex_cmds = [
            ['makeindex',
                '-s',
                'python.ist',
                '{0}.idx'.format(
                    os.path.splitext(os.path.relpath(tex_file, latex_cwd))[0])]
            for tex_file in tex_files]

        if self.build_env.command_class == DockerBuildCommand:
            latex_class = DockerLatexBuildCommand
        else:
            latex_class = LatexBuildCommand
        pdf_commands = []
        for cmd in pdflatex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class, cmd=cmd, cwd=latex_cwd, warn_only=True)
            pdf_commands.append(cmd_ret)
        for cmd in makeindex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class, cmd=cmd, cwd=latex_cwd, warn_only=True)
            pdf_commands.append(cmd_ret)
        for cmd in pdflatex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class, cmd=cmd, cwd=latex_cwd, warn_only=True)
            pdf_match = PDF_RE.search(cmd_ret.output)
            if pdf_match:
                self.pdf_file_name = pdf_match.group(1).strip()
            pdf_commands.append(cmd_ret)
        return all(cmd.successful for cmd in pdf_commands)

    def move(self, **__):
        if not os.path.exists(self.target):
            os.makedirs(self.target)

        exact = os.path.join(self.old_artifact_path, "%s.pdf" % self.project.slug)
        exact_upper = os.path.join(
            self.old_artifact_path,
            "%s.pdf" % self.project.slug.capitalize())

        if self.pdf_file_name and os.path.exists(self.pdf_file_name):
            from_file = self.pdf_file_name
        if os.path.exists(exact):
            from_file = exact
        elif os.path.exists(exact_upper):
            from_file = exact_upper
        else:
            from_globs = glob(os.path.join(self.old_artifact_path, "*.pdf"))
            if from_globs:
                from_file = max(from_globs, key=os.path.getmtime)
            else:
                from_file = None
        if from_file:
            to_file = os.path.join(self.target, "%s.pdf" % self.project.slug)
            self.run('mv', '-f', from_file, to_file)
