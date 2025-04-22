"""
Sphinx_ backend for building docs.

.. _Sphinx: http://www.sphinx-doc.org/
"""

import itertools
import os
from glob import glob
from pathlib import Path

import structlog

from readthedocs.projects.constants import OLD_LANGUAGES_CODE_MAPPING
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.exceptions import UserFileNotFound

from ..base import BaseBuilder
from ..constants import PDF_RE
from ..environments import BuildCommand
from ..environments import DockerBuildCommand
from ..exceptions import BuildUserError


log = structlog.get_logger(__name__)


class BaseSphinx(BaseBuilder):
    """The parent for most sphinx builders."""

    # Sphinx reads and parses all source files before it can write
    # an output file, the parsed source files are cached as "doctree pickles".
    sphinx_doctrees_dir = "_build/doctrees"

    # Output directory relative to $READTHEDOCS_OUTPUT
    # (e.g. "html", "htmlzip" or "pdf")
    relative_output_dir = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = self.config.sphinx.configuration

        # We cannot use `$READTHEDOCS_OUTPUT` environment variable for
        # `absolute_host_output_dir` because it's not defined in the host. So,
        # we have to re-calculate its value. We will remove this limitation
        # when we execute the whole building from inside the Docker container
        # (instead behing a hybrid as it is now)
        #
        # We need to have two different paths that point to the exact same
        # directory. How is that? The directory is mounted into a different
        # location inside the container:
        #
        #  1. path in the host:
        #       /home/docs/checkouts/readthedocs.org/user_builds/<project>/
        #  2. path in the container:
        #       /usr/src/app/checkouts/readthedocs.org/user_builds/b9cbc24c8841/test-builds/
        #
        # Besides, the variable `$READTHEDOCS_OUTPUT` is not defined in the
        # host, so we have to expand it using the full host's path. This
        # variable cannot be used in cwd= due to a limitation of the Docker API
        # (I guess) since I received an error when trying that. So, we have to
        # fully expand it.
        #
        # That said, we need:
        #
        # * use the path in the host, for all the operations that are done via
        # Python from the app (e.g. os.path.join, glob.glob, etc)
        #
        # * use the path in the container, for all the operations that are
        # executed inside the container via Docker API using shell commands
        self.absolute_host_output_dir = os.path.join(
            os.path.join(
                self.project.checkout_path(self.version.slug),
                "_readthedocs/",
            ),
            self.relative_output_dir,
        )
        self.absolute_container_output_dir = os.path.join(
            "$READTHEDOCS_OUTPUT", self.relative_output_dir
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

    def get_language(self, project):
        """Get a Sphinx compatible language code."""
        language = project.language
        return OLD_LANGUAGES_CODE_MAPPING.get(language, language)

    def show_conf(self):
        """Show the current ``conf.py`` being used."""
        if self.config_file is None:
            raise ProjectConfigurationError(ProjectConfigurationError.NOT_FOUND)

        self.config_file = self.config_file or self.project.conf_file(self.version.slug)

        if not os.path.exists(self.config_file):
            raise UserFileNotFound(
                message_id=UserFileNotFound.FILE_NOT_FOUND,
                format_values={
                    "filename": os.path.relpath(self.config_file, self.project_path),
                },
            )

        # Print the contents of conf.py in order to make the rendered
        # configfile visible in the build logs
        self.run(
            "cat",
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
            "-T",
        ]
        if self.config.sphinx.fail_on_warning:
            build_command.extend(["-W", "--keep-going"])
        language = self.get_language(project)
        build_command.extend(
            [
                "-b",
                self.sphinx_builder,
                "-d",
                self.sphinx_doctrees_dir,
                "-D",
                f"language={language}",
                # Sphinx's source directory (SOURCEDIR).
                # We are executing this command at the location of the `conf.py` file (CWD).
                # TODO: ideally we should execute it from where the repository was clonned,
                # but that could lead unexpected behavior to some users:
                # https://github.com/readthedocs/readthedocs.org/pull/9888#issuecomment-1384649346
                ".",
                # Sphinx's output build directory (OUTPUTDIR)
                self.absolute_container_output_dir,
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
            self.python_env.venv_bin(filename="python"),
            "-m",
            "sphinx",
        )


class HtmlBuilder(BaseSphinx):
    relative_output_dir = "html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = "html"


class HtmlDirBuilder(HtmlBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = "dirhtml"


class SingleHtmlBuilder(HtmlBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sphinx_builder = "singlehtml"


class LocalMediaBuilder(BaseSphinx):
    sphinx_builder = "singlehtml"
    relative_output_dir = "htmlzip"

    def _post_build(self):
        """Internal post build to create the ZIP file from the HTML output."""
        target_file = os.path.join(
            self.absolute_container_output_dir,
            # TODO: shouldn't this name include the name of the version as well?
            # It seems we were using the project's slug previously.
            # So, keeping it like that for now until we decide make that adjustment.
            f"{self.project.slug}.zip",
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
            self.absolute_container_output_dir,
            str(tmp_dir / dirname),
            cwd=self.project_path,
            record=False,
        )
        self.run(
            "mkdir",
            "--parents",
            self.absolute_container_output_dir,
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
    relative_output_dir = "epub"

    def _post_build(self):
        """Internal post build to cleanup EPUB output directory and leave only one .epub file."""
        temp_epub_file = f"/tmp/{self.project.slug}-{self.version.slug}.epub"
        target_file = os.path.join(
            self.absolute_container_output_dir,
            f"{self.project.slug}.epub",
        )

        epub_sphinx_filepaths = glob(os.path.join(self.absolute_host_output_dir, "*.epub"))
        if epub_sphinx_filepaths:
            # NOTE: we currently support only one .epub per version
            epub_filepath = epub_sphinx_filepaths[0]

            self.run("mv", epub_filepath, temp_epub_file, cwd=self.project_path, record=False)
            self.run(
                "rm",
                "--recursive",
                self.absolute_container_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mkdir",
                "--parents",
                self.absolute_container_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run("mv", temp_epub_file, target_file, cwd=self.project_path, record=False)


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

    relative_output_dir = "pdf"
    sphinx_builder = "latex"
    pdf_file_name = None

    def build(self):
        language = self.get_language(self.project)
        self.run(
            *self.get_sphinx_cmd(),
            "-T",
            "-b",
            self.sphinx_builder,
            "-d",
            self.sphinx_doctrees_dir,
            "-D",
            f"language={language}",
            # Sphinx's source directory (SOURCEDIR).
            # We are executing this command at the location of the `conf.py` file (CWD).
            # TODO: ideally we should execute it from where the repository was clonned,
            # but that could lead unexpected behavior to some users:
            # https://github.com/readthedocs/readthedocs.org/pull/9888#issuecomment-1384649346
            ".",
            # Sphinx's output build directory (OUTPUTDIR)
            self.absolute_container_output_dir,
            cwd=os.path.dirname(self.config_file),
            bin_path=self.python_env.venv_bin(),
        )

        tex_files = glob(os.path.join(self.absolute_host_output_dir, "*.tex"))
        if not tex_files:
            raise BuildUserError(message_id=BuildUserError.TEX_FILE_NOT_FOUND)

        # Run LaTeX -> PDF conversions
        success = self._build_latexmk(self.project_path)

        self._post_build()
        return success

    def _build_latexmk(self, cwd):
        # These steps are copied from the Makefile generated by Sphinx >= 1.6
        # https://github.com/sphinx-doc/sphinx/blob/master/sphinx/texinputs/Makefile_t
        images = []
        for extension in ("png", "gif", "jpg", "jpeg"):
            images.extend(Path(self.absolute_host_output_dir).glob(f"*.{extension}"))

        # FIXME: instead of checking by language here, what we want to check if
        # ``latex_engine`` is ``platex``
        pdfs = []
        if self.project.language == "ja":
            # Japanese language is the only one that requires this extra
            # step. I don't know exactly why but most of the documentation that
            # I read differentiate this language from the others. I suppose
            # it's because it mix kanji (Chinese) with its own symbols.
            pdfs = Path(self.absolute_host_output_dir).glob("*.pdf")

        for image in itertools.chain(images, pdfs):
            self.run(
                "extractbb",
                image.name,
                cwd=self.absolute_host_output_dir,
                record=False,
            )

        rcfile = "latexmkrc"
        if self.project.language == "ja":
            rcfile = "latexmkjarc"

        self.run(
            "cat",
            rcfile,
            cwd=self.absolute_host_output_dir,
        )

        if self.build_env.command_class == DockerBuildCommand:
            latex_class = DockerLatexBuildCommand
        else:
            latex_class = LatexBuildCommand

        cmd = [
            "latexmk",
            "-r",
            rcfile,
            # FIXME: check for platex here as well
            "-pdfdvi" if self.project.language == "ja" else "-pdf",
            # When ``-f`` is used, latexmk will continue building if it
            # encounters errors. We still receive a failure exit code in this
            # case, but the correct steps should run.
            "-f",
            "-dvi-",
            "-ps-",
            f"-jobname={self.project.slug}",
            "-interaction=nonstopmode",
        ]

        cmd_ret = self.build_env.run_command_class(
            cls=latex_class,
            cmd=cmd,
            warn_only=True,
            cwd=self.absolute_host_output_dir,
        )

        self.pdf_file_name = f"{self.project.slug}.pdf"

        return cmd_ret.successful

    def _post_build(self):
        """Internal post build to cleanup PDF output directory and leave only one .pdf file."""

        if not self.pdf_file_name:
            raise BuildUserError(BuildUserError.PDF_NOT_FOUND)

        # TODO: merge this with ePUB since it's pretty much the same
        temp_pdf_file = f"/tmp/{self.project.slug}-{self.version.slug}.pdf"
        target_file = os.path.join(
            self.absolute_container_output_dir,
            self.pdf_file_name,
        )

        # NOTE: we currently support only one .pdf per version
        pdf_sphinx_filepath = os.path.join(self.absolute_container_output_dir, self.pdf_file_name)
        pdf_sphinx_filepath_host = os.path.join(
            self.absolute_host_output_dir,
            self.pdf_file_name,
        )
        if os.path.exists(pdf_sphinx_filepath_host):
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
                self.absolute_container_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run(
                "mkdir",
                "-p",
                self.absolute_container_output_dir,
                cwd=self.project_path,
                record=False,
            )
            self.run("mv", temp_pdf_file, target_file, cwd=self.project_path, record=False)
