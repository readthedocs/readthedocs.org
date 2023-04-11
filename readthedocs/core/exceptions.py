from django.http import Http404


class ContextualizedHttp404(Http404):

    template_name = "errors/404/base.html"

    def __init__(self, **kwargs):
        self.context = kwargs


class ProjectHttp404(ContextualizedHttp404):

    """Raised if a project was not found."""

    template_name = "errors/404/no_project.html"


class SubProjectHttp404(ContextualizedHttp404):

    """Raised if a subproject was not found."""

    template_name = "errors/404/no_subproject.html"


class ProjectPageHttp404(ContextualizedHttp404):

    """Raised if a page inside an existing project was not found."""

    template_name = "errors/404/no_project_page.html"


class ProjectTranslationHttp404(ContextualizedHttp404):

    """
    Raised if a translation of a project was not found.

    This means that the project does not exist for requested language.
    If a page isn't found, raise a ProjectPageHttp404.
    """

    template_name = "errors/404/no_language.html"


class ProjectVersionHttp404(ContextualizedHttp404):

    """
    Raised if a version was not found.

    Note: The containing project can be both a project or a subproject inside another project.
    """

    template_name = "errors/404/no_version.html"
