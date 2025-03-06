from readthedocs.doc_builder.exceptions import BuildUserError


class ConfigError(BuildUserError):
    GENERIC = "config:generic"
    DEFAULT_PATH_NOT_FOUND = "config:path:default-not-found"
    CONFIG_PATH_NOT_FOUND = "config:path:not-found"
    KEY_NOT_SUPPORTED_IN_VERSION = "config:key:not-supported-in-version"
    PYTHON_SYSTEM_PACKAGES_REMOVED = "config:python:system-packages-removed"
    PYTHON_USE_SYSTEM_SITE_PACKAGES_REMOVED = "config:python:use-system-site-packages-removed"
    INVALID_VERSION = "config:base:invalid-version"
    NOT_BUILD_TOOLS_OR_COMMANDS = "config:build:missing-build-tools-commands"
    BUILD_JOBS_AND_COMMANDS = "config:build:jobs-and-commands"
    BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS = "config:build:jobs:build:missing-in-formats"
    APT_INVALID_PACKAGE_NAME_PREFIX = "config:apt:invalid-package-name-prefix"
    APT_INVALID_PACKAGE_NAME = "config:apt:invalid-package-name"
    USE_PIP_FOR_EXTRA_REQUIREMENTS = "config:python:pip-required"
    PIP_PATH_OR_REQUIREMENT_REQUIRED = "config:python:pip-path-requirement-required"
    SPHINX_MKDOCS_CONFIG_TOGETHER = "config:base:sphinx-mkdocs-together"
    SUBMODULES_INCLUDE_EXCLUDE_TOGETHER = "config:submodules:include-exclude-together"
    INVALID_KEY_NAME = "config:base:invalid-key-name"
    SYNTAX_INVALID = "config:base:invalid-syntax"
    CONDA_KEY_REQUIRED = "config:conda:required"

    SPHINX_CONFIG_MISSING = "config:sphinx:missing-config"
    MKDOCS_CONFIG_MISSING = "config:mkdocs:missing-config"


# TODO: improve these error messages shown to the user
# See https://github.com/readthedocs/readthedocs.org/issues/10502
class ConfigValidationError(BuildUserError):
    INVALID_BOOL = "config:validation:invalid-bool"
    INVALID_CHOICE = "config:validation:invalid-choice"
    INVALID_DICT = "config:validation:invalid-dict"
    INVALID_PATH = "config:validation:invalid-path"
    INVALID_PATH_PATTERN = "config:validation:invalid-path-pattern"
    INVALID_STRING = "config:validation:invalid-string"
    INVALID_LIST = "config:validation:invalid-list"
    VALUE_NOT_FOUND = "config:validation:value-not-found"
