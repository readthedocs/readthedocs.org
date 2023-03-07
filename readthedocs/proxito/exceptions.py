"""
Exceptions for El Proxito.

This module contains exceptions that may be raised in El Proxito application
but are handled elsewhere in the Django project.

--------------
404 exceptions
--------------

Because an Http404 can be raised anywhere in the code,
we want to add more context for targeted error handling and user-facing communication
"""
from django.http.response import Http404


class ProxitoHttp404(Http404):

    """General error class for proxity 404s."""


class ProxitoProjectHttp404(ProxitoHttp404):

    """Raised if a project was not found."""

    def __init__(self, message, project_slug=None, proxito_path=None):
        self.project_slug = project_slug
        self.proxito_path = proxito_path
        super().__init__(message)


class ProxitoSubProjectHttp404(ProxitoProjectHttp404):

    """Raised if a subproject was not found."""

    def __init__(
        self,
        message,
        project_slug=None,
        proxito_path=None,
        project=None,
        subproject_slug=None,
    ):
        super().__init__(message, project_slug=project_slug, proxito_path=proxito_path)
        self.project = project
        self.subproject_slug = subproject_slug


class ProxitoProjectPageHttp404(ProxitoProjectHttp404):

    """Raised if a page inside an existing project was not found."""

    def __init__(
        self,
        message,
        project_slug=None,
        proxito_path=None,
        project=None,
        subproject_slug=None,
    ):
        super().__init__(message, project_slug=project_slug, proxito_path=proxito_path)
        self.project = project
        self.subproject_slug = subproject_slug


class ProxitoProjectTranslationHttp404(ProxitoProjectHttp404):

    """
    Raised if a translation of a project was not found.

    This means that the project does not exist for requested language.
    If a page isn't found, raise a ProxitoProjectPageHttp404.
    """

    def __init__(
        self,
        message,
        project_slug=None,
        proxito_path=None,
        project=None,
        subproject_slug=None,
        translation_slug=None,
    ):
        super().__init__(message, project_slug=project_slug, proxito_path=proxito_path)
        self.project = project
        self.subproject_slug = subproject_slug
        self.translation_slug = translation_slug


class ProxitoProjectVersionHttp404(ProxitoProjectHttp404):

    """
    Raised if a version was not found.

    Note: The containing project can be both a project or a subproject inside another project.
    """

    def __init__(
        self,
        message,
        project_slug=None,
        proxito_path=None,
        project=None,
        subproject_slug=None,
        version_slug=None,
    ):
        super().__init__(message, project_slug=project_slug, proxito_path=proxito_path)
        self.project = project
        self.subproject_slug = subproject_slug
        self.version_slug = version_slug
