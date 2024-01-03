"""Notifications related to Read the Docs YAML config file."""

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import ERROR
from readthedocs.notifications.messages import Message, registry

from .exceptions import ConfigError, ConfigValidationError

# General errors
messages = [
    Message(
        id=ConfigError.GENERIC,
        header=_("There was an unexpected problem in your config file"),
        body=_(
            """
            There was an unexpected problem in your config file.
            Make sure the encoding is correct.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.DEFAULT_PATH_NOT_FOUND,
        header=_("Config file not found at default path"),
        body=_(
            """
            No default configuration file found at repository's root.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.CONFIG_PATH_NOT_FOUND,
        header=_("Configuration file not found"),
        body=_(
            """
            Configuration file not found in <code>{directory}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.KEY_NOT_SUPPORTED_IN_VERSION,
        header=_("Configuration key not supported in this version"),
        body=_(
            """
            The <code>{key}</code> configuration option is not supported in this version.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PYTHON_SYSTEM_PACKAGES_REMOVED,
        header=_("Invalid configuration key"),
        body=_(
            """
            The configuration key <code>python.system_packages</code> has been deprecated and removed.
            Refer to https://blog.readthedocs.com/drop-support-system-packages/ to read more
            about this change and how to upgrade your config file."
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PYTHON_USE_SYSTEM_SITE_PACKAGES_REMOVED,
        header=_("Invalid configuration key"),
        body=_(
            """
            The configuration key <code>python.use_system_site_packages</code> has been deprecated and removed.
            Refer to https://blog.readthedocs.com/drop-support-system-packages/ to read more
            about this change and how to upgrade your config file."
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.INVALID_VERSION,
        header=_("Invalid configuration version"),
        body=_(
            """
            Invalid version of the configuration file.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.GENERIC_INVALID_CONFIG_KEY,
        header=_("Invalid configuration option"),
        body=_(
            """
            Invalid configuration option: <code>{key}</code>.

            Read the Docs configuration file: <code>{source_file}</code>.

            <code>{error_message}</code>
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.NOT_BUILD_TOOLS_OR_COMMANDS,
        header=_("Invalid configuration option: <code>build</code>"),
        body=_(
            """
            At least one item should be provided in "tools" or "commands".
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.BUILD_JOBS_AND_COMMANDS,
        header=_("Invalid configuration option"),
        body=_(
            """
            The keys <code>build.jobs</code> and <code>build.commands</code> can't be used together.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.APT_INVALID_PACKAGE_NAME_PREFIX,
        header=_("Invalid APT package name"),
        body=_(
            """
            The name of the packages (e.g. <code>{package}</code>) can't start with <code>{prefix}</code>
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.APT_INVALID_PACKAGE_NAME,
        header=_("Invalid APT package name"),
        body=_(
            """
            The name of the package <code>{pacakge}</name> is invalid.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.USE_PIP_FOR_EXTRA_REQUIREMENTS,
        header=_("Invalid Python install method"),
        body=_(
            """
            You need to install your project with pip to use <code>extra_requirements</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.PIP_PATH_OR_REQUIREMENT_REQUIRED,
        header=_("Invalid configuration key"),
        body=_(
            """
            <code>path</code> or <code>requirements</code> key is required for <code>python.install</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SPHINX_MKDOCS_CONFIG_TOGETHER,
        header=_("Invalid configuration key"),
        body=_(
            """
            You can not have <code>sphinx</code> and <code>mkdocs</code> keys at the same time.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SUBMODULES_INCLUDE_EXCLUDE_TOGETHER,
        header=_("Invalid configuration key"),
        body=_(
            """
            You can not have <code>exclude</code> and <code>include</code> submodules at the same time.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.INVALID_KEY_NAME,
        header=_("Invalid configuration key: {key}"),
        body=_(
            """
            Make sure the key name <code>{key}</code> is correct.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.SYNTAX_INVALID,
        header=_("Invalid syntax in configuration file"),
        body=_(
            """
            Error while parsing <code>{filename}</code>.

            {error_message}
            """
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
            """
            Config validation error in <code>{key}</code>.
            Expected one of (0, 1, true, false), got <code>{value}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_CHOICE,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            Expected one of ({choices}), got <code>{value}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_DICT,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            Expected a dictionary, got <code>{value}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_PATH,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            The path <code>{value}</code> does not exist.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_PATH_PATTERN,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            The path <code>{value}</code> is not a valid path pattern.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_STRING,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            Expected a string, got <code>{value}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.INVALID_LIST,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            Expected a list, got <code>{value}</code>.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigValidationError.VALUE_NOT_FOUND,
        header=_("Config file validation error"),
        body=_(
            """
            Config validation error in <code>{key}</code>.
            Value <code>{value}</code> not found.
            """
        ),
        type=ERROR,
    ),
]
registry.add(messages)
