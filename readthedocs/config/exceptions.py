from readthedocs.doc_builder.exceptions import BuildUserError


class ConfigError(BuildUserError):
    GENERIC = "config:generic"
    DEFAULT_PATH_NOT_FOUND = "config:path:default-not-found"
    CONFIG_PATH_NOT_FOUND = "config:path:not-found"
    KEY_NOT_SUPPORTED_IN_VERSION = "config:key:not-supported-in-version"
    PYTHON_SYSTEM_PACKAGES_REMOVED = "config:python:system-packages-removed"
    PYTHON_USE_SYSTEM_SITE_PACKAGES_REMOVED = (
        "config:python:use-system-site-packages-removed"
    )
    INVALID_VERSION = "config:base:invalid-version"
    GENERIC_INVALID_CONFIG_KEY = "config:key:generic-invalid-config-key"
    NOT_BUILD_TOOLS_OR_COMMANDS = "config:build:missing-build-tools-commands"
    BUILD_JOBS_AND_COMMANDS = "config:build:jobs-and-commands"
    APT_INVALID_PACKAGE_NAME_PREFIX = "config:apt:invalid-package-name-prefix"
    APT_INVALID_PACKAGE_NAME = "config:apt:invalid-package-name"
    USE_PIP_FOR_EXTRA_REQUIREMENTS = "config:python:pip-required"
    PIP_PATH_OR_REQUIREMENT_REQUIRED = "config:python:pip-path-requirement-required"
    SPHINX_MKDOCS_CONFIG_TOGETHER = "config:base:sphinx-mkdocs-together"
    SUBMODULES_INCLUDE_EXCLUDE_TOGETHER = "config:submodules:include-exclude-together"
    INVALID_KEY_NAME = "config:base:invalid-key-name"
    SYNTAX_INVALID = "config:base:invalid-syntax"
