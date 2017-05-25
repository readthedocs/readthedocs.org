"""Exceptions raised when building documentation."""


class BuildEnvironmentException(Exception):

    def __init__(self, *args, **kwargs):
        self.status_code = kwargs.pop('status_code', 1)
        super(BuildEnvironmentException, self).__init__(*args, **kwargs)


class BuildEnvironmentError(BuildEnvironmentException):
    pass


class BuildEnvironmentWarning(BuildEnvironmentException):
    pass
