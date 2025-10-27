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

    sphinx_doctrees_dir = "_build/doctrees"
    relative_output_dir = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = self.config.sphinx.configuration

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
                ".",
                self.absolute_container_output_dir,
            ]
        )

        # --- Added for Sphinx tags ---
        # Try to detect tags defined in conf.py and add them to the build command
        try:
            conf_namespace = {}
            with open(self.config_file, "r", encoding="utf-8") as f:
                exec(f.read(), conf_namespace)
            tags = conf_namespace.get("tags", [])
            if hasattr(tags, "tags"):  # Handle `from sphinx.application import Tags`
                tags = list(tags.tags)
            if isinstance(tags, (list, set, tuple)):
                for tag in tags:
                    build_command.extend(["-t", str(tag)])
        except Exception as e:
            log.warning("Could not parse tags from conf.py", error=str(e))
        # --- End of Sphinx tags addition ---

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
        target_file = os.path.join(
            self.absolute_container_output_dir,
            f"{self.project.slug}.zip",
        )
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
            "--recurse-paths",
            "--symlinks",
            target_file,
            dirname,
            cwd=str(tmp_dir),
            record=False,
        )


class EpubBuilder(BaseSphinx):
    sphinx_builder = "epub"
    relative_output_dir = "epub"

    def _post_build(self):
        temp_epub_file = f"/tmp/{self.project.slug}-{self.version.slug}.epub"
        target_file = os.path.join(
            self.absolute_container_output_dir,
            f"{self.project.slug}.epub",
        )
        epub_sphinx_filepaths = glob(os.path.join(self.absolute_host_output_dir, "*.epub"))
        if epub_sphinx_filepaths:
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
        if PDF_RE.search(self.output):
            self.exit_code = 0


class DockerLatexBuildCommand(DockerBuildCommand):
    """Ignore LaTeX exit code if there was file output."""

    def run(self):
        super().run()
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
            ".",
            self.absolute_container_output_dir,
            cwd=os.path.dirname(self.config_file),
            bin_path=self.python_env.venv_bin(),
        )

        tex_files = glob(os.path.join(self.absolute_host_output_dir, "*.tex"))
        if not tex_files:
            raise BuildUserError(message_id=BuildUserError.TEX_FILE_NOT_FOUND)

        success = self._build_latexmk(self.project_path)
        self._post_build()
        return success

    def _build_latexmk(self, cwd):
        images = []
        for extension in ("png", "gif", "jpg", "jpeg"):
            images.extend(Path(self.absolute_host_output_dir).glob(f"*.{extension}"))
        pdfs = []
        if self.project.language == "ja":
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

        self.run("cat", rcfile, cwd=self.absolute_host_output_dir)

        if self.build_env.command_class == DockerBuildCommand:
            latex_class = DockerLatexBuildCommand
        else:
            latex_class = LatexBuildCommand

        cmd = [
            "latexmk",
            "-r",
            rcfile,
            "-pdfdvi" if self.project.language == "ja" else "-pdf",
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
        if not self.pdf_file_name:
            raise BuildUserError(BuildUserError.PDF_NOT_FOUND)
        temp_pdf_file = f"/tmp/{self.project.slug}-{self.version.slug}.pdf"
        target_file = os.path.join(
            self.absolute_container_output_dir,
            self.pdf_file_name,
        )
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
