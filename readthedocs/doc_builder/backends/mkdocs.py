"""
MkDocs_ backend for building docs.

.. _MkDocs: http://www.mkdocs.org/
"""

import os

import structlog
import yaml
from django.conf import settings
from django.template import loader as template_loader

from readthedocs.core.utils.filesystem import safe_open
from readthedocs.doc_builder.base import BaseBuilder
from readthedocs.doc_builder.exceptions import MkDocsYAMLParseError
from readthedocs.projects.constants import MKDOCS, MKDOCS_HTML
from readthedocs.projects.exceptions import UserFileNotFound
from readthedocs.projects.models import Feature

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
        self.yaml_file = self.get_yaml_config()

        # README: historically, the default theme was ``readthedocs`` but in
        # https://github.com/rtfd/readthedocs.org/pull/4556 we change it to
        # ``mkdocs`` to maintain the same behavior in Read the Docs than
        # building locally. Although, we can't apply this into the Corporate
        # site. To keep the same default theme there, we created a Feature flag
        # for these project that were building with MkDocs in the Corporate
        # site.
        if self.project.has_feature(Feature.MKDOCS_THEME_RTD):
            self.DEFAULT_THEME_NAME = "readthedocs"
            log.warning(
                "Project using readthedocs theme as default for MkDocs.",
                project_slug=self.project.slug,
            )
        else:
            self.DEFAULT_THEME_NAME = "mkdocs"

    def get_final_doctype(self):
        """
        Select a doctype based on the ``use_directory_urls`` setting.

        https://www.mkdocs.org/user-guide/configuration/#use_directory_urls
        """
        # Allow symlinks, but only the ones that resolve inside the base directory.
        with safe_open(
            self.yaml_file, "r", allow_symlinks=True, base_path=self.project_path
        ) as fh:
            config = yaml_load_safely(fh)
            use_directory_urls = config.get("use_directory_urls", True)
            return MKDOCS if use_directory_urls else MKDOCS_HTML

    def get_yaml_config(self):
        """Find the ``mkdocs.yml`` file in the project root."""
        mkdocs_path = self.config.mkdocs.configuration
        if not mkdocs_path:
            mkdocs_path = "mkdocs.yml"
        return os.path.join(
            self.project_path,
            mkdocs_path,
        )

    def load_yaml_config(self):
        """
        Load a YAML config.

        :raises: ``MkDocsYAMLParseError`` if failed due to syntax errors.
        """
        try:
            # Allow symlinks, but only the ones that resolve inside the base directory.
            result = safe_open(
                self.yaml_file, "r", allow_symlinks=True, base_path=self.project_path
            )
            if not result:
                raise UserFileNotFound(
                    message_id=UserFileNotFound.FILE_NOT_FOUND,
                    format_values={
                        "filename": self.yaml_file,
                    },
                )

            config = yaml_load_safely(result)

            if not config:
                raise MkDocsYAMLParseError(MkDocsYAMLParseError.EMPTY_CONFIG)
            if not isinstance(config, dict):
                raise MkDocsYAMLParseError(MkDocsYAMLParseError.CONFIG_NOT_DICT)
            return config

        except IOError:
            raise MkDocsYAMLParseError(MkDocsYAMLParseError.NOT_FOUND)
        except yaml.YAMLError as exc:
            note = ""
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                note = " (line %d, column %d)" % (
                    mark.line + 1,
                    mark.column + 1,
                )
            raise MkDocsYAMLParseError(
                MkDocsYAMLParseError.SYNTAX_ERROR,
            ) from exc

    def append_conf(self):
        """
        Set mkdocs config values.

        :raises: ``MkDocsYAMLParseError`` if failed due to known type errors
                 (i.e. expecting a list and a string is found).
        """
        user_config = self.load_yaml_config()

        # Handle custom docs dirs
        docs_dir = user_config.get("docs_dir", "docs")
        if not isinstance(docs_dir, (type(None), str)):
            raise MkDocsYAMLParseError(
                MkDocsYAMLParseError.INVALID_DOCS_DIR_CONFIG,
            )

        user_config["docs_dir"] = docs_dir
        static_url = self.project.proxied_static_path

        # Set mkdocs config values.
        extra_assets = {
            "extra_javascript": [
                "readthedocs-data.js",
                f"{static_url}core/js/readthedocs-doc-embed.js",
                f"{static_url}javascript/readthedocs-analytics.js",
            ],
            "extra_css": [
                f"{static_url}css/badge_only.css",
                f"{static_url}css/readthedocs-doc-embed.css",
            ],
        }

        for config, extras in extra_assets.items():
            value = user_config.get(config, [])
            if value is None:
                value = []
            if not isinstance(value, list):
                raise MkDocsYAMLParseError(
                    message_id=MkDocsYAMLParseError.INVALID_EXTRA_CONFIG,
                    format_values={
                        "extra_config": config,
                    },
                )
            # Add the static file only if isn't already in the list.
            value.extend([extra for extra in extras if extra not in value])
            user_config[config] = value

        # The docs path is relative to the location
        # of the mkdocs configuration file.
        docs_path = os.path.join(
            os.path.dirname(self.yaml_file),
            docs_dir,
        )

        # if user puts an invalid `docs_dir` path raise an Exception
        if not os.path.exists(docs_path):
            raise MkDocsYAMLParseError(
                MkDocsYAMLParseError.INVALID_DOCS_DIR_PATH,
            )

        # RTD javascript writing
        rtd_data = self.generate_rtd_data(
            docs_dir=os.path.relpath(docs_path, self.project_path),
            mkdocs_config=user_config,
        )
        with safe_open(
            os.path.join(docs_path, "readthedocs-data.js"), "w", encoding="utf-8"
        ) as f:
            f.write(rtd_data)

        # Use Read the Docs' analytics setup rather than mkdocs'
        # This supports using RTD's privacy improvements around analytics
        user_config["google_analytics"] = None

        # README: make MkDocs to use ``readthedocs`` theme as default if the
        # user didn't specify a specific theme manually
        if self.project.has_feature(Feature.MKDOCS_THEME_RTD):
            if "theme" not in user_config:
                # mkdocs<0.17 syntax
                user_config["theme"] = self.DEFAULT_THEME_NAME

        # Write the modified mkdocs configuration
        with safe_open(self.yaml_file, "w", encoding="utf-8") as f:
            yaml_dump_safely(
                user_config,
                f,
            )

        # Write the mkdocs.yml to the build logs
        self.run(
            "cat",
            os.path.relpath(self.yaml_file, self.project_path),
            cwd=self.project_path,
        )

    def generate_rtd_data(self, docs_dir, mkdocs_config):
        """Generate template properties and render readthedocs-data.js."""
        # Use the analytics code from mkdocs.yml
        # if it isn't set already by Read the Docs,
        analytics_code = self.version.project.analytics_code
        if not analytics_code and mkdocs_config.get("google_analytics"):
            # http://www.mkdocs.org/user-guide/configuration/#google_analytics
            analytics_code = mkdocs_config["google_analytics"][0]

        commit = (
            self.version.project.vcs_repo(
                version=self.version.slug,
                environment=self.build_env,
            ).commit,
        )

        # Will be available in the JavaScript as READTHEDOCS_DATA.
        readthedocs_data = {
            "project": self.version.project.slug,
            "version": self.version.slug,
            "language": self.version.project.language,
            "programming_language": self.version.project.programming_language,
            "page": None,
            "theme": self.get_theme_name(mkdocs_config),
            "builder": "mkdocs",
            "docroot": docs_dir,
            "source_suffix": ".md",
            "api_host": settings.PUBLIC_API_URL,
            "ad_free": not self.project.show_advertising,
            "commit": commit,
            "global_analytics_code": (
                None
                if self.project.analytics_disabled
                else settings.GLOBAL_ANALYTICS_CODE
            ),
            "user_analytics_code": analytics_code,
            "proxied_static_path": self.project.proxied_static_path,
            "proxied_api_host": self.project.proxied_api_host,
        }

        data_ctx = {
            "readthedocs_data": readthedocs_data,
            "current_version": readthedocs_data["version"],
            "slug": readthedocs_data["project"],
            "html_theme": readthedocs_data["theme"],
            "pagename": None,
        }
        tmpl = template_loader.get_template("doc_builder/data.js.tmpl")
        return tmpl.render(data_ctx)

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
            os.path.relpath(self.yaml_file, self.project_path),
        ]
        if self.config.mkdocs.fail_on_warning:
            build_command.append("--strict")
        cmd_ret = self.run(
            *build_command,
            cwd=self.project_path,
            bin_path=self.python_env.venv_bin(),
        )
        return cmd_ret.successful

    def get_theme_name(self, mkdocs_config):
        """
        Get the theme configuration in the mkdocs_config.

        In v0.17.0, the theme configuration switched
        from two separate configs (both optional) to a nested directive.

        :see: http://www.mkdocs.org/about/release-notes/#theme-customization-1164
        :returns: the name of the theme RTD will use
        """
        theme_setting = mkdocs_config.get("theme")
        if isinstance(theme_setting, dict):
            # Full nested theme config (the new configuration)
            return theme_setting.get("name") or self.DEFAULT_THEME_NAME

        if theme_setting:
            # A string which is the name of the theme
            return theme_setting

        theme_dir = mkdocs_config.get("theme_dir")
        if theme_dir:
            # Use the name of the directory in this project's custom theme directory
            return theme_dir.rstrip("/").split("/")[-1]

        return self.DEFAULT_THEME_NAME


class MkdocsHTML(BaseMkdocs):
    builder = "build"
    build_dir = "_readthedocs/html"


# TODO: find a better way to integrate with MkDocs.
# See https://github.com/readthedocs/readthedocs.org/issues/7844


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


SafeLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", SafeLoader.construct_python_name
)
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


def yaml_dump_safely(content, stream=None):
    """Uses ``SafeDumper`` dumper to write YAML contents."""
    return yaml.dump(content, stream=stream, Dumper=SafeDumper)
