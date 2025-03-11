"""Notifications related to Read the Docs YAML config file."""

import textwrap

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import ERROR
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry

from .exceptions import ConfigError
from .exceptions import ConfigValidationError


# General errors
messages = [
    Message(
        id=ConfigError.GENERIC,
        header=_("There was an unexpected problem in your config file"),
        body=_(
            textwrap.dedent(
                """
            There was an unexpected problem in your config file.
            Make sure the encoding is correct.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.DEFAULT_PATH_NOT_FOUND,
        header=_("Config file not found at default path"),
        body=_(
            textwrap.dedent(
                """
            The required <code>.readthedocs.yaml</code> configuration file was not found at repository's root.
            Learn how to use this file in our <a href="https://docs.readthedocs.io/en/stable/config-file/index.html">configuration file tutorial</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.CONFIG_PATH_NOT_FOUND,
        header=_("Configuration file not found"),
        body=_(
            textwrap.dedent(
                """
            Configuration file not found in <code>{{directory}}</code>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.KEY_NOT_SUPPORTED_IN_VERSION,
        header=_("Configuration key not supported in this version"),
        body=_(
            textwrap.dedent(
                """
            The <code>{{key}}</code> configuration option is not supported in this version.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PYTHON_SYSTEM_PACKAGES_REMOVED,
        header=_("Invalid configuration key"),
        body=_(
            textwrap.dedent(
                """
            The configuration key <code>python.system_packages</code> has been deprecated and removed.
            <a href="https://blog.readthedocs.com/drop-support-system-packages/">Read our blog post</a>
            to learn more about this change and how to upgrade your configuration file."
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PYTHON_USE_SYSTEM_SITE_PACKAGES_REMOVED,
        header=_("Invalid configuration key"),
        body=_(
            textwrap.dedent(
                """
            The configuration key <code>python.use_system_site_packages</code> has been deprecated and removed.
            <a href="https://blog.readthedocs.com/drop-support-system-packages/">Read our blog post</a>
            to learn more about this change and how to upgrade your configuration file."
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.INVALID_VERSION,
        header=_("Invalid configuration version"),
        body=_(
            textwrap.dedent(
                """
            Invalid version of the configuration file.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.NOT_BUILD_TOOLS_OR_COMMANDS,
        header=_("Missing configuration option"),
        body=_(
            textwrap.dedent(
                """
            At least one of the following configuration options is required: <code>build.tools</code> or <code>build.commands</code>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.BUILD_JOBS_AND_COMMANDS,
        header=_("Invalid configuration option"),
        body=_(
            textwrap.dedent(
                """
            The keys <code>build.jobs</code> and <code>build.commands</code> can't be used together.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS,
        header=_("Invalid configuration option"),
        body=_(
            textwrap.dedent(
                """
                The <code>{{ build_type }}</code> build type was defined in <code>build.jobs.build</code>, but it wasn't included in <code>formats</code>.
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.APT_INVALID_PACKAGE_NAME_PREFIX,
        header=_("Invalid APT package name"),
        body=_(
            textwrap.dedent(
                """
            The name of the packages (e.g. <code>{{package}}</code>) can't start with <code>{{prefix}}</code>
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.APT_INVALID_PACKAGE_NAME,
        header=_("Invalid APT package name"),
        body=_(
            textwrap.dedent(
                """
            The name of the package <code>{{pacakge}}</code> is invalid.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.USE_PIP_FOR_EXTRA_REQUIREMENTS,
        header=_("Invalid Python install method"),
        body=_(
            textwrap.dedent(
                """
            You need to install your project with <code>python.install.method: pip</code>
            to use <code>python.install.extra_requirements</code>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PIP_PATH_OR_REQUIREMENT_REQUIRED,
        header=_("Missing configuration key"),
        body=_(
            textwrap.dedent(
                """
                When using <code>python.install</code>,
                one of the following keys are required: <code>python.install.path</code> or <code>python.install.requirements</code>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SPHINX_MKDOCS_CONFIG_TOGETHER,
        header=_("Invalid configuration key"),
        body=_(
            textwrap.dedent(
                """
            You can not have <code>sphinx</code> and <code>mkdocs</code> keys at the same time.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SUBMODULES_INCLUDE_EXCLUDE_TOGETHER,
        header=_("Invalid configuration key"),
        body=_(
            textwrap.dedent(
                """
            You can not have <code>submodules.exclude</code> and <code>submodules.include</code> at the same time.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.INVALID_KEY_NAME,
        header=_("Invalid configuration key: {{key}}"),
        body=_(
            textwrap.dedent(
                """
            Make sure the key name <code>{{key}}</code> is correct.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SYNTAX_INVALID,
        header=_("Invalid syntax in configuration file"),
        body=_(
            textwrap.dedent(
                """
            Error while parsing <code>{{filename}}</code>.
            Make sure your configuration file doesn't have any errors.

            {{error_message}}
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.CONDA_KEY_REQUIRED,
        header=_("Missing required key"),
        body=_(
            textwrap.dedent(
                """
            The key <code>conda.environment</code> is required when using Conda or Mamba.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
]
registry.add(messages)

# Validation errors
messages = [
    Message(
        id=ConfigValidationError.INVALID_BOOL,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Expected one of <code>[0, 1, true, false]</code>, got type <code>{{value|to_class_name}}</code> (<code>{{value}}</code>).
            Make sure the type of the value is not a string.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_CHOICE,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Expected one of ({{choices}}), got type <code>{{value|to_class_name}}</code> (<code>{{value}}</code>).
            Double check the type of the value.
            A string may be required (e.g. <code>"3.10"</code> instead of <code>3.10</code>)
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_DICT,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Expected a dictionary, got type <code>{{value|to_class_name}}</code> (<code>{{value}}</code>).
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_PATH,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            The path <code>{{value}}</code> does not exist.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_PATH_PATTERN,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            The path <code>{{value}}</code> is not a valid path pattern.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_STRING,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Expected a string, got type <code>{{value|to_class_name}}</code> (<code>{{value}}</code>).
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_LIST,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Expected a list, got type <code>{{value|to_class_name}}</code> (<code>{{value}}</code>).
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.VALUE_NOT_FOUND,
        header=_("Config file validation error"),
        body=_(
            textwrap.dedent(
                """
            Config validation error in <code>{{key}}</code>.
            Value <code>{{value}}</code> not found.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SPHINX_CONFIG_MISSING,
        header=_("Missing Sphinx configuration key"),
        body=_(
            textwrap.dedent(
                """
                The <code>sphinx.configuration</code> key is missing.
                This key is now required, see our <a href="https://about.readthedocs.com/blog/2024/12/deprecate-config-files-without-sphinx-or-mkdocs-config/">blog post</a> for more information.
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.MKDOCS_CONFIG_MISSING,
        header=_("Missing MkDocs configuration key"),
        body=_(
            textwrap.dedent(
                """
                The <code>mkdocs.configuration</code> key is missing.
                This key is now required, see our <a href="https://about.readthedocs.com/blog/2024/12/deprecate-config-files-without-sphinx-or-mkdocs-config/">blog post</a> for more information.
                """
            ).strip(),
        ),
        type=ERROR,
    ),
]
registry.add(messages)
