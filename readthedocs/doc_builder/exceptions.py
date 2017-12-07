"""Exceptions raised when building documentation."""

from django.utils.translation import ugettext_noop


class BuildEnvironmentException(Exception):

    message = None

    def __init__(self, message=None, **kwargs):
        self.status_code = kwargs.pop('status_code', 1)
        message = message or self.get_default_message()
        super(BuildEnvironmentException, self).__init__(message, **kwargs)

    def get_default_message(self):
        return self.message


class BuildEnvironmentError(BuildEnvironmentException):

    GENERIC_WITH_BUILD_ID = ugettext_noop(
        "There was a problem with Read the Docs while building your documentation. "
        "Please report this to us with your build id ({build_id})."
    )


class BuildEnvironmentCreationFailed(BuildEnvironmentError):

    message = ugettext_noop(
        "Build environment creation failed"
    )


class BuildEnvironmentWarning(BuildEnvironmentException):
    pass
