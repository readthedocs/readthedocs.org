"""Project exceptions"""
from __future__ import absolute_import, division, print_function


class ProjectImportError (Exception):

    """Failure to import a project from a repository."""

    pass


class ProjectSpamError(Exception):

    """Error raised when a project field has detected spam"""

    pass
