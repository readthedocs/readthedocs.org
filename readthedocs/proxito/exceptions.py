from django.http import Http404
from django.utils.translation import pgettext_lazy


class ContextualizedHttp404(Http404):

    """
    Base class for contextualized HTTP 404 handling.

    Subclasses may define their own template name,
    HTTP status and object that was not found.

    The contextualized exception is handled by proxito's 404 handler
    """

    template_name = "errors/404/base.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "page"
    )

    def __init__(self, http_status=404, path_not_found=None, **kwargs):
        """
        Constructor that all subclasses should call.

        :param kwargs: all kwargs are added as page context for rendering the 404 template
        :param http_status: 404 view should respect this and set the HTTP status.
        :param path_not_found: Inform the template and 404 view about a different path from
                               request.path
        """
        self.http_status = kwargs.pop("http_status", 404)
        self.path_not_found = kwargs.pop("path_not_found", None)
        self.kwargs = kwargs

    def get_context(self):
        c = {
            "not_found_subject": self.not_found_subject,
            "path_not_found": self.path_not_found,
        }
        c.update(self.kwargs)
        return c


class DomainDNSHttp404(ContextualizedHttp404):

    """Raised if a DNS record points to us and we don't know the domain."""

    template_name = "errors/404/dns.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "matching DNS record"
    )


class ProjectHttp404(ContextualizedHttp404):

    """
    Raised if a domain did not resolve to a project.

    This is currently used very broadly.
    It indicates a number of reasons for the user.
    """

    template_name = "errors/404/no_project.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "project"
    )


class SubprojectHttp404(ContextualizedHttp404):

    """Raised if a subproject was not found."""

    template_name = "errors/404/no_subproject.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "subproject"
    )


class ProjectFilenameHttp404(ContextualizedHttp404):

    """Raised if a page inside an existing project was not found."""

    template_name = "errors/404/no_project_page.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "documentation page"
    )


class ProjectTranslationHttp404(ContextualizedHttp404):

    """
    Raised if a translation of a project was not found.

    This means that the project does not exist for requested language.
    If a page isn't found, raise a ProjectPageHttp404.
    """

    template_name = "errors/404/no_language.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "translation"
    )


class ProjectVersionHttp404(ContextualizedHttp404):

    """
    Raised if a version was not found.

    Note: The containing project can be a subproject.
    """

    template_name = "errors/404/no_version.html"
    not_found_subject = pgettext_lazy(
        "Names an object not found in a 404 error", "documentation version"
    )
