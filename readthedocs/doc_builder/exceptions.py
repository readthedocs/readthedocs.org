# -*- coding: utf-8 -*-
"""Exceptions raised when building documentation."""

from __future__ import division, print_function, unicode_literals

from django.utils.translation import ugettext_noop


class BuildEnvironmentException(Exception):
    message = None
    status_code = None

    def __init__(self, message=None, **kwargs):
        self.status_code = kwargs.pop('status_code', None) or self.status_code or 1
        message = message or self.get_default_message()
        super(BuildEnvironmentException, self).__init__(message, **kwargs)

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
