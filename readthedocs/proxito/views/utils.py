import os
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .decorators import map_project_slug, map_subproject_slug

log = logging.getLogger(__name__)  # noqa


def fast_404(request, *args, **kwargs):
    """
    A fast error page handler.

    This stops us from running RTD logic in our error handling. We already do
    this in RTD prod when we fallback to it.
    """
    return HttpResponse('Not Found.', status=404)


def _fallback():
    # TODO: This currently isn't used. It might be though, so keeping it for now
    res = HttpResponse('Internal fallback to RTD app')
    res.status_code = 420
    log.debug('Falling back to RTD app')
    return res


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
    if final_project.single_version and not version_slug:
        version_slug = final_project.get_default_version()

    # ``final_project`` is now the actual project we want to serve docs on,
    # accounting for:
    # * Project
    # * Subproject
    # * Translations

    return final_project, lang_slug, version_slug, filename
