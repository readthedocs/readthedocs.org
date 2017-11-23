"""Exceptions raised when building documentation."""


class BuildEnvironmentException(Exception):

    message = None

    def __init__(self, message=None, **kwargs):
        self.status_code = kwargs.pop('status_code', 1)
        message = message or self.get_default_message()
        super(BuildEnvironmentException, self).__init__(message, **kwargs)

    def get_default_message(self):
        return self.message


class BuildEnvironmentError(BuildEnvironmentException):
    pass


class BuildEnvironmentWarning(BuildEnvironmentException):
    pass
