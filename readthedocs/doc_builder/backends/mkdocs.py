"""
MkDocs_ backend for building docs.
"""

import os

import structlog
import yaml
from django.conf import settings

from readthedocs.core.utils.filesystem import safe_open
from readthedocs.doc_builder.base import BaseBuilder
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.constants import MKDOCS_HTML
from readthedocs.projects.exceptions import UserFileNotFound


class BaseMkdocs(BaseBuilder):
    """
    MkDocs builder.

    This class and the following class use a different build method
    than the Sphinx builders. We don't use `make` and instead call
    the Python module directly.
    """

    type = "mkdocs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.project_path, self.config.mkdocs.build_dir
        )

        # This is the *MkDocs* yaml file
        self.yaml_file = self.get_yaml_config()

    def get_final_doctype(self):
        """
        Select a doctype based on the ``use_directory_urls`` setting.

        MkDocs produces a different style of html depending on the
        ``use_directory_urls`` setting. We use this to set the doctype.
        """
        with safe_open(self.yaml_file, "r") as f:
            config = yaml.safe_load(f)

        if config.get("use_directory_urls"):
            return MKDOCS_HTML
        return MKDOCS

    def get_yaml_config(self):
        """Find the MkDocs yaml configuration file."""
        # We support both `.yml` and `.yaml` extensions
        for extension in ["yml", "yaml"]:
            config_file = os.path.join(
                self.project_path, f"mkdocs.{extension}"
            )
            if os.path.exists(config_file):
                return config_file

        # If we didn't find any, return the default one
        return os.path.join(self.project_path, "mkdocs.yml")

    def build(self):
        build_command = [
            self.python_env.venv_bin(filename="python"),
            "-m",
            "mkdocs",
            "build",
            "--clean",
            "--site-dir",
            self.old_artifact_path,
            "--config-file",
            os.path.relpath(self.yaml_file, self.project_path),
        ]

        if self.config.mkdocs.fail_on_warning:
            build_command.append("--strict")
        cmd_ret = self.run(
            *build_command, cwd=self.project_path, bin_path=self.python_env.venv_bin()
        )
        return cmd_ret.success


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
