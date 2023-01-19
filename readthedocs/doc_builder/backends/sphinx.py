"""
Sphinx_ backend for building docs.

.. _Sphinx: http://www.sphinx-doc.org/
"""

import itertools
import os
from glob import glob
from pathlib import Path

import structlog
from django.conf import settings
from django.template import loader as template_loader
from django.template.loader import render_to_string
from django.urls import reverse
from requests.exceptions import ConnectionError

from readthedocs.api.v2.client import api
from readthedocs.builds import utils as version_utils
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.doc_builder.exceptions import PDFNotFound
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.exceptions import ProjectConfigurationError, UserFileNotFound
from readthedocs.projects.models import Feature
from readthedocs.projects.utils import safe_write

from ..base import BaseBuilder
from ..constants import PDF_RE
from ..environments import BuildCommand, DockerBuildCommand
from ..exceptions import BuildUserError
from ..signals import finalize_sphinx_context_data

log = structlog.get_logger(__name__)


class BaseSphinx(BaseBuilder):

    """The parent for most sphinx builders."""

    # Sphinx reads and parses all source files before it can write
    # an output file, the parsed source files are cached as "doctree pickles".
    sphinx_doctrees_dir = "_build/doctrees"

    # Output directory relative to where the repository was cloned
    # (e.g. "_readthedocs/<format>")
    relative_output_dir = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = self.config.sphinx.configuration
        self.absolute_output_dir = os.path.abspath(
            os.path.join(self.project_path, self.relative_output_dir)
        )
        try:
            if not self.config_file:
                self.config_file = self.project.conf_file(self.version.slug)
            else:
                self.config_file = os.path.join(
                    self.project_path,
                    self.config_file,
                )
        except ProjectConfigurationError:
            # NOTE: this exception handling here is weird to me.
            # We are raising this exception from inside `project.confi_file` when:
            #  - the repository has multiple config files (none of them with `doc` in its filename)
            #  - there is no config file at all
            #
            # IMO, if there are multiple config files,
            # the build should fail immediately communicating this to the user.
            # This can be achived by unhandle the exception here
            # and leaving `on_failure` Celery handle to deal with it.
            #
            # In case there is no config file, we should continue the build
            # because Read the Docs will automatically create one for it.
            pass

    def _write_config(self, master_doc='index'):
        """Create ``conf.py`` if it doesn't exist."""
        log.info(
            'Creating default Sphinx config file for project.',
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )
        docs_dir = self.docs_dir()
        conf_template = render_to_string(
            'sphinx/conf.py.conf',
            {
                'project': self.project,
                'version': self.version,
                'master_doc': master_doc,
            },
        )
        conf_file = os.path.join(docs_dir, 'conf.py')
        safe_write(conf_file, conf_template)

    def get_config_params(self):
        """Get configuration parameters to be rendered into the conf file."""
        # TODO this should be handled better in the theme
        conf_py_path = os.path.join(
            os.path.sep,
            os.path.dirname(
                os.path.relpath(
                    self.config_file,
                    self.project_path,
                ),
            ),
            '',
        )
        remote_version = self.version.commit_name

        github_user, github_repo = version_utils.get_github_username_repo(
            url=self.project.repo,
        )
        github_version_is_editable = (self.version.type == 'branch')
        display_github = github_user is not None

        bitbucket_user, bitbucket_repo = version_utils.get_bitbucket_username_repo(  # noqa
            url=self.project.repo,
        )
        bitbucket_version_is_editable = (self.version.type == 'branch')
        display_bitbucket = bitbucket_user is not None

        gitlab_user, gitlab_repo = version_utils.get_gitlab_username_repo(
            url=self.project.repo,
        )
        gitlab_version_is_editable = (self.version.type == 'branch')
        display_gitlab = gitlab_user is not None

        versions = []
        downloads = []
        subproject_urls = []
        # Avoid hitting database and API if using Docker build environment
        if settings.DONT_HIT_API:
            if self.project.has_feature(Feature.ALL_VERSIONS_IN_HTML_CONTEXT):
                versions = self.project.active_versions()
            else:
                versions = self.project.active_versions().filter(
                    privacy_level=PUBLIC,
                )
            downloads = self.version.get_downloads(pretty=True)
            subproject_urls = self.project.get_subproject_urls()
        else:
            try:
                versions = self.project.api_versions()
                if not self.project.has_feature(Feature.ALL_VERSIONS_IN_HTML_CONTEXT):
                    versions = [
                        v
                        for v in versions
                        if v.privacy_level == PUBLIC
                    ]
                downloads = api.version(self.version.pk).get()['downloads']
                subproject_urls = self.project.get_subproject_urls()
            except ConnectionError:
                log.exception(
                    'Timeout while fetching versions/downloads/subproject_urls for Sphinx context.',
                    project_slug=self.project.slug,
                    version_slug=self.version.slug,
                )

        build_id = self.build_env.build.get('id')
        build_url = None
        if build_id:
            build_url = reverse(
                'builds_detail',
                kwargs={
                    'project_slug': self.project.slug,
                    'build_pk': build_id,
                },
            )
            protocol = 'http' if settings.DEBUG else 'https'
            build_url = f'{protocol}://{settings.PRODUCTION_DOMAIN}{build_url}'

        vcs_url = None
        if self.version.is_external:
            vcs_url = self.version.vcs_url

        commit = (
            self.project.vcs_repo(
                version=self.version.slug,
                environment=self.build_env,
            )
            .commit
        )

        data = {
            "html_theme": "sphinx_rtd_theme",
            "html_theme_import": "sphinx_rtd_theme",
            "current_version": self.version.verbose_name,
            "project": self.project,
            "version": self.version,
            "settings": settings,
            "conf_py_path": conf_py_path,
            "api_host": settings.PUBLIC_API_URL,
            "commit": commit,
            "versions": versions,
            "downloads": downloads,
            "subproject_urls": subproject_urls,
            "build_url": build_url,
            "vcs_url": vcs_url,
            "proxied_static_path": self.project.proxied_static_path,
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

            # GitLab
            'gitlab_user': gitlab_user,
            'gitlab_repo': gitlab_repo,
            'gitlab_version': remote_version,
            'gitlab_version_is_editable': gitlab_version_is_editable,
            'display_gitlab': display_gitlab,

            # Features
            'dont_overwrite_sphinx_context': self.project.has_feature(
                Feature.DONT_OVERWRITE_SPHINX_CONTEXT,
            ),
            'docsearch_disabled': self.project.has_feature(Feature.DISABLE_SERVER_SIDE_SEARCH),
        }

        finalize_sphinx_context_data.send(
            sender=self.__class__,
            build_env=self.build_env,
            data=data,
        )

        return data

    def append_conf(self):
        """
        Find or create a ``conf.py`` and appends default content.

        The default content is rendered from ``doc_builder/conf.py.tmpl``.
        """
        if self.config_file is None:
            master_doc = self.create_index(extension='rst')
            self._write_config(master_doc=master_doc)

        try:
            self.config_file = (
                self.config_file or self.project.conf_file(self.version.slug)
            )
            # Allow symlinks, but only the ones that resolve inside the base directory.
            outfile = safe_open(
                self.config_file, "a", allow_symlinks=True, base_path=self.project_path
            )
            if not outfile:
                raise UserFileNotFound(
                    UserFileNotFound.FILE_NOT_FOUND.format(self.config_file)
                )
        except IOError:
            raise ProjectConfigurationError(ProjectConfigurationError.NOT_FOUND)

        # Append config to project conf file
        tmpl = template_loader.get_template('doc_builder/conf.py.tmpl')
        rendered = tmpl.render(self.get_config_params())

        with outfile:
            outfile.write('\n')
            outfile.write(rendered)

        # Print the contents of conf.py in order to make the rendered
        # configfile visible in the build logs
        self.run(
            'cat',
            os.path.relpath(
                self.config_file,
                self.project_path,
            ),
            cwd=self.project_path,
        )

    def build(self):
        project = self.project
        build_command = [
            *self.get_sphinx_cmd(),
            '-T',
            '-E',
            *self.sphinx_parallel_arg(),
        ]
        if self.config.sphinx.fail_on_warning:
            build_command.extend(["-W", "--keep-going"])
        build_command.extend(
            [
                "-b",
                self.sphinx_builder,
                "-d",
                self.sphinx_doctrees_dir,
                "-D",
                f"language={project.language}",
                # Sphinx's source directory (SOURCEDIR).
                # We are executing this command at the location of the `conf.py` file (CWD).
                # TODO: ideally we should execute it from where the repository was clonned,
                # but that could lead unexpected behavior to some users:
                # https://github.com/readthedocs/readthedocs.org/pull/9888#issuecomment-1384649346
                ".",
                # Sphinx's output build directory (OUTPUTDIR)
                os.path.relpath(
                    self.absolute_output_dir, os.path.dirname(self.config_file)
                ),
            ]
        )
        cmd_ret = self.run(
            *build_command,
            bin_path=self.python_env.venv_bin(),
            cwd=os.path.dirname(self.config_file),
        )

        self._post_build()

        return cmd_ret.successful

    def get_sphinx_cmd(self):
        return (
            self.python_env.venv_bin(filename='python'),
            '-m',
            'sphinx',
        )

    def sphinx_parallel_arg(self):
        if self.project.has_feature(Feature.SPHINX_PARALLEL):
            return ['-j', 'auto']
        return []

    def venv_sphinx_supports_latexmk(self):
        """
        Check if ``sphinx`` from the user's venv supports ``latexmk``.

        If the version of ``sphinx`` is greater or equal to 1.6.1 it returns
        ``True`` and ``False`` otherwise.

        See: https://www.sphinx-doc.org/en/master/changes.html#release-1-6-1-released-may-16-2017
        """

        command = [
            self.python_env.venv_bin(filename='python'),
            '-c',
            (
                '"'
                'import sys; '
                'import sphinx; '
                'sys.exit(0 if sphinx.version_info >= (1, 6, 1) else 1)'
                '"'
            ),
        ]

        cmd_ret = self.run(
            *command,
            bin_path=self.python_env.venv_bin(),
            cwd=self.project_path,
            escape_command=False,  # used on DockerBuildCommand
            shell=True,  # used on BuildCommand
            record=False,
        )
        return cmd_ret.exit_code == 0


class HtmlBuilder(BaseSphinx):
    relative_output_dir = "_readthedocs/html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = 'readthedocs'
        if self.project.has_feature(Feature.USE_SPHINX_BUILDERS):
            self.sphinx_builder = 'html'


class HtmlDirBuilder(HtmlBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = 'readthedocsdirhtml'
        if self.project.has_feature(Feature.USE_SPHINX_BUILDERS):
            self.sphinx_builder = 'dirhtml'


class SingleHtmlBuilder(HtmlBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = 'readthedocssinglehtml'
        if self.project.has_feature(Feature.USE_SPHINX_BUILDERS):
            self.sphinx_builder = 'singlehtml'


class LocalMediaBuilder(BaseSphinx):
    sphinx_builder = 'readthedocssinglehtmllocalmedia'
    relative_output_dir = "_readthedocs/htmlzip"

    def _post_build(self):
        """Internal post build to create the ZIP file from the HTML output."""
        target_file = os.path.abspath(
            os.path.join(
                self.absolute_output_dir,
                # TODO: shouldn't this name include the name of the version as well?
                # It seems we were using the project's slug previously.
                # So, keeping it like that for now until we decide make that adjustment.
                f"{self.project.slug}.zip",
            )
        )

        # **SECURITY CRITICAL: Advisory GHSA-hqwg-gjqw-h5wg**
        # Move the directory into a temporal directory,
        # so we can rename the directory for zip to use
        # that prefix when zipping the files (arcname).
        mktemp = self.run("mktemp", "--directory", record=False)
        tmp_dir = Path(mktemp.output.strip())
        dirname = f"{self.project.slug}-{self.version.slug}"
        self.run(
            "mv",
            self.relative_output_dir,
            str(tmp_dir / dirname),
            cwd=self.project_path,
            record=False,
        )
        self.run(
            "mkdir",
            "--parents",
            self.relative_output_dir,
            cwd=self.project_path,
            record=False,
        )
        self.run(
            "zip",
            "--recurse-paths",  # Include all files and directories.
            "--symlinks",  # Don't resolve symlinks.
            target_file,
            dirname,
            cwd=str(tmp_dir),
            record=False,
        )


class EpubBuilder(BaseSphinx):

    sphinx_builder = "epub"
    relative_output_dir = "_readthedocs/epub"

    def _post_build(self):
        """Internal post build to cleanup EPUB output directory and leave only one .epub file."""
        temp_epub_file = f"/tmp/{self.project.slug}-{self.version.slug}.epub"
        target_file = os.path.join(
            self.absolute_output_dir,
            f"{self.project.slug}.epub",
        )

        epub_sphinx_filepaths = glob(os.path.join(self.absolute_output_dir, "*.epub"))
        if epub_sphinx_filepaths:
            # NOTE: we currently support only one .epub per version
            epub_filepath = epub_sphinx_filepaths[0]

            self.run(
                "mv", epub_filepath, temp_epub_file, cwd=self.project_path, record=False
            )
            self.run(
                "rm",
                "--recursive",
                self.relative_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mkdir",
                "--parents",
                self.relative_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mv", temp_epub_file, target_file, cwd=self.project_path, record=False
            )


class LatexBuildCommand(BuildCommand):

    """Ignore LaTeX exit code if there was file output."""

    def run(self):
        super().run()
        # Force LaTeX exit code to be a little more optimistic. If LaTeX
        # reports an output file, let's just assume we're fine.
        if PDF_RE.search(self.output):
            self.exit_code = 0


class DockerLatexBuildCommand(DockerBuildCommand):

    """Ignore LaTeX exit code if there was file output."""

    def run(self):
        super().run()
        # Force LaTeX exit code to be a little more optimistic. If LaTeX
        # reports an output file, let's just assume we're fine.
        if PDF_RE.search(self.output):
            self.exit_code = 0


class PdfBuilder(BaseSphinx):

    """Builder to generate PDF documentation."""

    relative_output_dir = "_readthedocs/pdf"
    sphinx_builder = "latex"
    pdf_file_name = None

    def build(self):
        self.run(
            *self.get_sphinx_cmd(),
            "-T",
            "-E",
            *self.sphinx_parallel_arg(),
            "-b",
            self.sphinx_builder,
            "-d",
            self.sphinx_doctrees_dir,
            "-D",
            f"language={self.project.language}",
            # Sphinx's source directory (SOURCEDIR).
            # We are executing this command at the location of the `conf.py` file (CWD).
            # TODO: ideally we should execute it from where the repository was clonned,
            # but that could lead unexpected behavior to some users:
            # https://github.com/readthedocs/readthedocs.org/pull/9888#issuecomment-1384649346
            ".",
            # Sphinx's output build directory (OUTPUTDIR)
            os.path.relpath(
                self.absolute_output_dir, os.path.dirname(self.config_file)
            ),
            cwd=os.path.dirname(self.config_file),
            bin_path=self.python_env.venv_bin(),
        )

        tex_files = glob(os.path.join(self.absolute_output_dir, "*.tex"))
        if not tex_files:
            raise BuildUserError("No TeX files were found.")

        # Run LaTeX -> PDF conversions
        # Build PDF with ``latexmk`` if Sphinx supports it, otherwise fallback
        # to ``pdflatex`` to support old versions
        if self.venv_sphinx_supports_latexmk():
            success = self._build_latexmk(self.project_path)
        else:
            success = self._build_pdflatex(tex_files)

        self._post_build()
        return success

    def _build_latexmk(self, cwd):
        # These steps are copied from the Makefile generated by Sphinx >= 1.6
        # https://github.com/sphinx-doc/sphinx/blob/master/sphinx/texinputs/Makefile_t
        images = []
        for extension in ("png", "gif", "jpg", "jpeg"):
            images.extend(Path(self.absolute_output_dir).glob(f"*.{extension}"))

        # FIXME: instead of checking by language here, what we want to check if
        # ``latex_engine`` is ``platex``
        pdfs = []
        if self.project.language == 'ja':
            # Japanese language is the only one that requires this extra
            # step. I don't know exactly why but most of the documentation that
            # I read differentiate this language from the others. I suppose
            # it's because it mix kanji (Chinese) with its own symbols.
            pdfs = Path(self.absolute_output_dir).glob("*.pdf")

        for image in itertools.chain(images, pdfs):
            self.run(
                'extractbb',
                image.name,
                cwd=self.absolute_output_dir,
                record=False,
            )

        rcfile = 'latexmkrc'
        if self.project.language == 'ja':
            rcfile = 'latexmkjarc'

        self.run(
            'cat',
            rcfile,
            cwd=self.absolute_output_dir,
        )

        if self.build_env.command_class == DockerBuildCommand:
            latex_class = DockerLatexBuildCommand
        else:
            latex_class = LatexBuildCommand

        cmd = [
            'latexmk',
            '-r',
            rcfile,
            # FIXME: check for platex here as well
            '-pdfdvi' if self.project.language == 'ja' else '-pdf',
            # When ``-f`` is used, latexmk will continue building if it
            # encounters errors. We still receive a failure exit code in this
            # case, but the correct steps should run.
            '-f',
            '-dvi-',
            '-ps-',
            f'-jobname={self.project.slug}',
            '-interaction=nonstopmode',
        ]

        cmd_ret = self.build_env.run_command_class(
            cls=latex_class,
            cmd=cmd,
            warn_only=True,
            cwd=self.absolute_output_dir,
        )

        self.pdf_file_name = f'{self.project.slug}.pdf'

        return cmd_ret.successful

    def _build_pdflatex(self, tex_files):
        pdflatex_cmds = [
            ['pdflatex', '-interaction=nonstopmode', tex_file]
            for tex_file in tex_files
        ]  # yapf: disable
        makeindex_cmds = [
            [
                "makeindex",
                "-s",
                "python.ist",
                "{}.idx".format(
                    os.path.splitext(
                        os.path.relpath(tex_file, self.absolute_output_dir)
                    )[0],
                ),
            ]
            for tex_file in tex_files
        ]  # yapf: disable

        if self.build_env.command_class == DockerBuildCommand:
            latex_class = DockerLatexBuildCommand
        else:
            latex_class = LatexBuildCommand
        pdf_commands = []
        for cmd in pdflatex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class,
                cmd=cmd,
                cwd=self.absolute_output_dir,
                warn_only=True,
            )
            pdf_commands.append(cmd_ret)
        for cmd in makeindex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class,
                cmd=cmd,
                cwd=self.absolute_output_dir,
                warn_only=True,
            )
            pdf_commands.append(cmd_ret)
        for cmd in pdflatex_cmds:
            cmd_ret = self.build_env.run_command_class(
                cls=latex_class,
                cmd=cmd,
                cwd=self.absolute_output_dir,
                warn_only=True,
            )
            pdf_match = PDF_RE.search(cmd_ret.output)
            if pdf_match:
                self.pdf_file_name = pdf_match.group(1).strip()
            pdf_commands.append(cmd_ret)
        return all(cmd.successful for cmd in pdf_commands)

    def _post_build(self):
        """Internal post build to cleanup PDF output directory and leave only one .pdf file."""

        if not self.pdf_file_name:
            raise PDFNotFound()

        # TODO: merge this with ePUB since it's pretty much the same
        temp_pdf_file = f"/tmp/{self.project.slug}-{self.version.slug}.pdf"
        target_file = os.path.join(
            self.absolute_output_dir,
            self.pdf_file_name,
        )

        # NOTE: we currently support only one .pdf per version
        pdf_sphinx_filepath = os.path.join(self.absolute_output_dir, self.pdf_file_name)
        if os.path.exists(pdf_sphinx_filepath):
            self.run(
                "mv",
                pdf_sphinx_filepath,
                temp_pdf_file,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "rm",
                "-r",
                self.relative_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mkdir",
                "-p",
                self.relative_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mv", temp_pdf_file, target_file, cwd=self.project_path, record=False
            )
