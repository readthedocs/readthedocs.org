"""
This module contains exceptions that may be raised in the proxito application
but are handled elsewhere in the Django project.

--------------
404 exceptions
--------------

Because an Http404 can be raised anywhere in the code,
we want to add more context for targeted error handling and user-facing communication
"""
from django.http.response import Http404


class ProxitoHttp404(Http404):
    """
    General error class for proxity 404s
    """

    def __init__(self, message):
        super().__init__(message)


class ProxitoProjectHttp404(ProxitoHttp404):
    """
    Raised if a project was not found
    """

    def __init__(self, message, project_slug=None):
        self.project_slug = project_slug
        super().__init__(message)


class ProxitoSubProjectHttp404(ProxitoProjectHttp404):
    """
    Raised if a sub-project was not found
    """
    def __init__(self, message, project_slug=None, project=None, subproject_slug=None):
        self.project_slug = project_slug
        self.project = project
        self.subproject_slug = subproject_slug
        super().__init__(message)


class ProxitoProjectPageHttp404(ProxitoHttp404):
    """
    Raised if a page inside an existing project was not found

    Note: The containing project can be both a project or a subproject inside another project
    """

    def __init__(self, message, project_slug=None, project=None, subproject_slug=None):
        self.project_slug = project_slug
        self.project = project
        self.subproject_slug = subproject_slug
        super().__init__(message)
