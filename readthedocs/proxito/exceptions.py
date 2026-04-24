from django.http import Http404
from django.utils.translation import pgettext_lazy


_not_found_subject_translation_context = (
    "Names a subject that was not found in a 404 error message. Used like "
    "'The {{ not_found_subject }} you are looking for at <code>{{ path_not_found }}</code> "
    "was not found.'"
)


class ContextualizedHttp404(Http404):
    """
    Base class for contextualized HTTP 404 handling.

    Subclasses may define their own template name,
    HTTP status and object that was not found.

    The contextualized exception is handled by proxito's 404 handler
    """

    template_name = "errors/proxito/404/base.html"
    not_found_subject = pgettext_lazy(_not_found_subject_translation_context, "page")

    def __init__(self, http_status=404, path_not_found=None, **kwargs):
        """
        Constructor that all subclasses should call.

        :param kwargs: all kwargs are added as page context for rendering the 404 template
        :param http_status: 404 view should respect this and set the HTTP status.
        :param path_not_found: Inform the template and 404 view about a different path from
                               request.path
        """
        self.http_status = http_status
        self.path_not_found = path_not_found
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

    template_name = "errors/proxito/404/dns.html"
    not_found_subject = pgettext_lazy(_not_found_subject_translation_context, "domain")

    def __init__(self, domain, **kwargs):
        """
        Raised when DNS for a custom domain is bad.

        :param domain: The domain for which DNS is misconfigured.
        :param kwargs:
        """
        kwargs["domain"] = domain
        super().__init__(**kwargs)


# All the following exceptions use the same template from ext-theme.
# That template uses `not_found_subject` as a heading and copy of the page,
# the rest of the page is exactly the same.
# This can be tested by using `DEBUG = False` in El Proxito.
class ProjectHttp404(ContextualizedHttp404):
    """
    Raised if a domain did not resolve to a project.

    This is currently used very broadly.
    It indicates a number of reasons for the user.
    """

    template_name = "errors/proxito/404/no_project.html"
    not_found_subject = pgettext_lazy(_not_found_subject_translation_context, "project")

    def __init__(self, domain, **kwargs):
        """
        Raised when a project wasn't found for a given domain.

        :param domain: The domain (custom and hosted) that was not found.
        :param kwargs:
        """
        kwargs["domain"] = domain
        super().__init__(**kwargs)


class SubprojectHttp404(ContextualizedHttp404):
    """Raised if a subproject was not found."""

    template_name = "errors/proxito/404/no_project.html"
    not_found_subject = pgettext_lazy("Names an object not found in a 404 error", "subproject")

    def __init__(self, project, **kwargs):
        """
        Raised if a subproject was not found.

        :param project: The project in which the subproject could not be found
        :param kwargs: Context dictionary of the rendered template
        """
        kwargs["project"] = project
        super().__init__(**kwargs)


class ProjectFilenameHttp404(ContextualizedHttp404):
    """Raised if a page inside an existing project was not found."""

    template_name = "errors/proxito/404/no_project.html"
    not_found_subject = pgettext_lazy(_not_found_subject_translation_context, "documentation page")

    def __init__(self, project, **kwargs):
        """
        Raised if a page inside an existing project was not found.

        :param project: The project in which the file could not be found
        :param kwargs: Context dictionary of the rendered template
        """
        kwargs["project"] = project
        super().__init__(**kwargs)


class ProjectTranslationHttp404(ContextualizedHttp404):
    """
    Raised if a translation of a project was not found.

    This means that the project does not exist for requested language.
    If a page isn't found, raise a ProjectPageHttp404.
    """

    template_name = "errors/proxito/404/no_project.html"
    not_found_subject = pgettext_lazy("Names an object not found in a 404 error", "translation")

    def __init__(self, project, **kwargs):
        """
        Raised if a translation of a project was not found.

        :param project: The project in which the translation could not be found
        :param kwargs: Context dictionary of the rendered template
        """
        kwargs["project"] = project
        super().__init__(**kwargs)


class ProjectVersionHttp404(ContextualizedHttp404):
    """
    Raised if a version was not found.

    Note: The containing project can be a subproject.
    """

    template_name = "errors/proxito/404/no_project.html"
    not_found_subject = pgettext_lazy(
        _not_found_subject_translation_context, "documentation version"
    )

    def __init__(self, project, **kwargs):
        """
        Raised if a version was not found.

        :param project: The project in which the version could not be found
        :param kwargs: Context dictionary of the rendered template
        """
        kwargs["project"] = project
        super().__init__(**kwargs)
