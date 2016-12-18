"""Project exceptions"""


class ProjectImportError (Exception):

    """Failure to import a project from a repository."""

    pass


class ProjectSpamError(Exception):

    """Error raised when a project field has detected spam"""

    pass
