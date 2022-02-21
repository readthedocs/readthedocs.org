# -*- coding: utf-8 -*-

"""Exceptions raised when building documentation."""

from django.utils.translation import gettext_noop
from readthedocs.core.exceptions import ReadTheDocsBaseException
from readthedocs.builds.constants import BUILD_STATUS_DUPLICATED


class BuildAppError(ReadTheDocsBaseException):
    GENERIC_WITH_BUILD_ID = gettext_noop(
        'There was a problem with Read the Docs while building your documentation. '
        'Please try again later. '
        'If this problem persists, '
        'report this error to us with your build id ({build_id}).',
    )


class BuildUserError(ReadTheDocsBaseException):
    GENERIC = gettext_noop(
        "We encountered a problem with a command while building your project. "
        "To resolve this error, double check your project configuration and installed "
        "dependencies are correct and have not changed recently."
    )


class ProjectBuildsSkippedError(BuildUserError):
    message = gettext_noop('Builds for this project are temporarily disabled')


class YAMLParseError(BuildUserError):
    GENERIC_WITH_PARSE_EXCEPTION = gettext_noop(
        'Problem in your project\'s configuration. {exception}',
    )


class BuildMaxConcurrencyError(BuildUserError):
    message = gettext_noop('Concurrency limit reached ({limit}), retrying in 5 minutes.')


class DuplicatedBuildError(BuildUserError):
    message = gettext_noop('Duplicated build.')
    exit_code = 1
    status = BUILD_STATUS_DUPLICATED


class MkDocsYAMLParseError(BuildUserError):
    GENERIC_WITH_PARSE_EXCEPTION = gettext_noop(
        'Problem parsing MkDocs YAML configuration. {exception}',
    )

    INVALID_DOCS_DIR_CONFIG = gettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file has to be a '
        'string with relative or absolute path.',
    )

    INVALID_DOCS_DIR_PATH = gettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file does not '
        'contain a valid path.',
    )

    INVALID_EXTRA_CONFIG = gettext_noop(
        'The "{config}" config from your MkDocs YAML config file has to be a '
        'a list of relative paths.',
    )

    EMPTY_CONFIG = gettext_noop(
        'Please make sure the MkDocs YAML configuration file is not empty.',
    )

    CONFIG_NOT_DICT = gettext_noop(
        'Your MkDocs YAML config file is incorrect. '
        'Please follow the user guide https://www.mkdocs.org/user-guide/configuration/ '
        'to configure the file properly.',
    )
