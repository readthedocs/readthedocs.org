# -*- coding: utf-8 -*-

"""Exceptions raised when building documentation."""

from django.utils.translation import ugettext_noop


class BuildEnvironmentException(Exception):
    message = None
    status_code = None

    def __init__(self, message=None, **kwargs):
        self.status_code = kwargs.pop(
            'status_code',
            None,
        ) or self.status_code or 1
        message = message or self.get_default_message()
        super().__init__(message, **kwargs)

    def get_default_message(self):
        return self.message


class BuildEnvironmentError(BuildEnvironmentException):
    GENERIC_WITH_BUILD_ID = ugettext_noop(
        'There was a problem with Read the Docs while building your documentation. '
        'Please try again later. '
        'However, if this problem persists, '
        'please report this to us with your build id ({build_id}).',
    )


class BuildEnvironmentCreationFailed(BuildEnvironmentError):
    message = ugettext_noop('Build environment creation failed')


class VersionLockedError(BuildEnvironmentError):
    message = ugettext_noop('Version locked, retrying in 5 minutes.')
    status_code = 423


class ProjectBuildsSkippedError(BuildEnvironmentError):
    message = ugettext_noop('Builds for this project are temporarily disabled')


class YAMLParseError(BuildEnvironmentError):
    GENERIC_WITH_PARSE_EXCEPTION = ugettext_noop(
        'Problem in your project\'s configuration. {exception}',
    )


class BuildTimeoutError(BuildEnvironmentError):
    message = ugettext_noop('Build exited due to time out')


class BuildEnvironmentWarning(BuildEnvironmentException):
    pass


class MkDocsYAMLParseError(BuildEnvironmentError):
    GENERIC_WITH_PARSE_EXCEPTION = ugettext_noop(
        'Problem parsing MkDocs YAML configuration. {exception}',
    )

    INVALID_DOCS_DIR_CONFIG = ugettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file has to be a '
        'string with relative or absolute path.',
    )

    INVALID_DOCS_DIR_PATH = ugettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file does not '
        'contain a valid path.',
    )

    INVALID_EXTRA_CONFIG = ugettext_noop(
        'The "{config}" config from your MkDocs YAML config file has to be a '
        'a list of relative paths.',
    )
