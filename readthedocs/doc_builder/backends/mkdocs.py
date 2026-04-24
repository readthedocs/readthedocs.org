"""
MkDocs_ backend for building docs.

.. _MkDocs: http://www.mkdocs.org/
"""

import os

import structlog
import yaml
from django.conf import settings

from readthedocs.doc_builder.base import BaseBuilder
from readthedocs.projects.exceptions import UserFileNotFound


log = structlog.get_logger(__name__)


def get_absolute_static_url():
    """
    Get the fully qualified static URL from settings.

    Mkdocs needs a full domain because it tries to link to local files.
    """
    static_url = settings.STATIC_URL

    if not static_url.startswith("http"):
        domain = settings.PRODUCTION_DOMAIN
        static_url = "http://{}{}".format(domain, static_url)

    return static_url


class BaseMkdocs(BaseBuilder):
    """Mkdocs builder."""

    # The default theme for mkdocs is the 'mkdocs' theme
    DEFAULT_THEME_NAME = "mkdocs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This is the *MkDocs* yaml file
        self.config_file = os.path.join(
            self.project_path,
            self.config.mkdocs.configuration,
        )

    def show_conf(self):
        """Show the current ``mkdocs.yaml`` being used."""
        if not os.path.exists(self.config_file):
            raise UserFileNotFound(
                message_id=UserFileNotFound.FILE_NOT_FOUND,
                format_values={
                    "filename": os.path.relpath(self.config_file, self.project_path),
                },
            )

        # Write the mkdocs.yml to the build logs
        self.run(
            "cat",
            os.path.relpath(self.config_file, self.project_path),
            cwd=self.project_path,
        )

    def build(self):
        build_command = [
            self.python_env.venv_bin(filename="python"),
            "-m",
            "mkdocs",
            self.builder,
            "--clean",
            "--site-dir",
            os.path.join("$READTHEDOCS_OUTPUT", "html"),
            "--config-file",
            os.path.relpath(self.config_file, self.project_path),
        ]

        if self.config.mkdocs.fail_on_warning:
            build_command.append("--strict")
        cmd_ret = self.run(
            *build_command,
            cwd=self.project_path,
            bin_path=self.python_env.venv_bin(),
        )
        return cmd_ret.successful


class MkdocsHTML(BaseMkdocs):
    builder = "build"
    build_dir = "_readthedocs/html"


class ProxyPythonName(yaml.YAMLObject):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value


class SafeLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
    """
    Safe YAML loader.

    This loader parses special ``!!python/name:`` tags without actually
    importing or executing code. Every other special tag is ignored.

    Borrowed from https://stackoverflow.com/a/57121993
    Issue https://github.com/readthedocs/readthedocs.org/issues/7461
    """

    def ignore_unknown(self, node):  # pylint: disable=unused-argument
        return None

    def construct_python_name(self, suffix, node):  # pylint: disable=unused-argument
        return ProxyPythonName(suffix)


class SafeDumper(yaml.SafeDumper):
    """
    Safe YAML dumper.

    This dumper allows to avoid losing values of special tags that
    were parsed by our safe loader.
    """

    def represent_name(self, data):
        return self.represent_scalar("tag:yaml.org,2002:python/name:" + data.value, "")


SafeLoader.add_multi_constructor("tag:yaml.org,2002:python/name:", SafeLoader.construct_python_name)
SafeLoader.add_constructor(None, SafeLoader.ignore_unknown)
SafeDumper.add_representer(ProxyPythonName, SafeDumper.represent_name)


def yaml_load_safely(content):
    """
    Uses ``SafeLoader`` loader to skip unknown tags.

    When a YAML contains ``!!python/name:int`` it will store the ``int``
    suffix temporarily to be able to re-dump it later. We need this to avoid
    executing random code, but still support these YAML files without
    information loss.
    """
    return yaml.load(content, Loader=SafeLoader)
