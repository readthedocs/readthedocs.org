from urllib.parse import urlparse

from django.http import HttpResponseRedirect

from readthedocs.core.resolver import resolve

from .decorators import map_project_slug, map_subproject_slug


@map_project_slug
@map_subproject_slug
def redirect_page_with_filename(request, project, subproject, filename):  # pylint: disable=unused-argument  # noqa
    """
    Redirect /page/file.html to.

    /<default-lang>/<default-version>/file.html.
    """

    urlparse_result = urlparse(request.get_full_path())
    return HttpResponseRedirect(
        resolve(
            subproject or project,
            filename=filename,
            query_params=urlparse_result.query,
        )
    )


@map_project_slug
@map_subproject_slug
def redirect_project_slug(request, project, subproject):  # pylint: disable=unused-argument
    """Handle / -> /en/latest/ directs on subdomains."""
    urlparse_result = urlparse(request.get_full_path())

    return HttpResponseRedirect(
        resolve(
            subproject or project,
            query_params=urlparse_result.query,
        ),
    )
