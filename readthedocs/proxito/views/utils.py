import os
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .decorators import map_project_slug, map_subproject_slug

log = logging.getLogger(__name__)  # noqa


def fast_404(request, *args, **kwargs):
    """
    A fast error page handler.

    This stops us from running RTD logic in our error handling. We already do
    this in RTD prod when we fallback to it.
    """
    return HttpResponse('Not Found.', status=404)


def proxito_404_page_handler(request, exception=None, template_name='404.html'):
    """
    Decide what 404 page return depending if it's an internal NGINX redirect.

    We want to return fast when the 404 is used as an internal NGINX redirect to
    reach our ``ServeError404`` view. However, if the 404 exception was risen
    inside ``ServeError404`` view, we want to render the default Read the Docs
    Maze page.
    """

    if request.resolver_match and request.resolver_match.url_name != 'proxito_404_handler':
        return fast_404(request, exception, template_name)

    resp = render(request, template_name)
    resp.status_code = 404
    return resp


@map_project_slug
@map_subproject_slug
def _get_project_data_from_request(
        request,
        project,
        subproject,
        lang_slug=None,
        version_slug=None,
        filename='',
):
    """
    Get the proper project based on the request and URL.

    This is used in a few places and so we break out into a utility function.
    """
    # Take the most relevant project so far
    current_project = subproject or project

    # Handle single-version projects that have URLs like a real project
    if current_project.single_version:
        if lang_slug and version_slug:
            filename = os.path.join(lang_slug, version_slug, filename)
            log.warning(
                'URL looks like versioned on a single version project.'
                'Changing filename to match. filename=%s',
                filename
            )
            lang_slug = version_slug = None

    # Check to see if we need to serve a translation
    if not lang_slug or lang_slug == current_project.language:
        final_project = current_project
    else:
        final_project = get_object_or_404(
            current_project.translations.all(), language=lang_slug
        )

    # Handle single version by grabbing the default version
    # We might have version_slug when we're serving a PR
    if any([
        not version_slug and final_project.single_version,
        not version_slug and project.urlconf and '$version' not in project.urlconf
    ]):
        version_slug = final_project.get_default_version()

    # Automatically add the default language if it isn't defined in urlconf
    if not lang_slug and project.urlconf and '$language' not in project.urlconf:
        lang_slug = final_project.language

    # ``final_project`` is now the actual project we want to serve docs on,
    # accounting for:
    # * Project
    # * Subproject
    # * Translations

    # Set the version slug on the request so we can log it in middleware
    request.path_version_slug = version_slug

    return final_project, lang_slug, version_slug, filename
