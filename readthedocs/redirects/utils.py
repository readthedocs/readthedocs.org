"""
Redirection view support.

This module allows for parsing a URL path, looking up redirects associated
with it in the database, and generating a redirect response.

These are not used directly as views; they are instead included into 404
handlers, so that redirects only take effect if no other view matches.
"""
import logging
import re
from urllib.parse import urlparse, urlunparse

from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from readthedocs.constants import LANGUAGES_REGEX
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


def project_and_path_from_request(request, path):
    """
    Parse the project from a request path.

    Return a tuple (project, path) where `project` is a projects.Project if
    a matching project exists, and `path` is the unmatched remainder of the
    path.

    If the path does not match, or no matching project is found, then `project`
    will be ``None``.
    """
    if hasattr(request, 'slug'):
        project_slug = request.slug
    elif path.startswith('/docs/'):
        # In this case we use the docs without subdomains. So let's strip the
        # docs prefix.
        match = re.match(
            r'^/docs/(?P<project_slug>[^/]+)(?P<path>/.*)$',
            path,
        )
        if match:
            project_slug = match.groupdict()['project_slug']
            path = match.groupdict()['path']
        else:
            return None, path
    else:
        return None, path

    try:
        project = Project.objects.get(slug=project_slug)
    except Project.DoesNotExist:
        return None, path
    return project, path


def language_and_version_from_path(path):
    match = re.match(
        r'^/(?P<language>%s)/(?P<version_slug>[^/]+)(?P<path>/.*)$' % LANGUAGES_REGEX,
        path,
    )
    if match:
        language = match.groupdict()['language']
        version_slug = match.groupdict()['version_slug']
        path = match.groupdict()['path']
        return language, version_slug, path
    return None, None, path


def get_redirect_response(request, full_path):
    project, full_path = project_and_path_from_request(request, full_path)
    if not project:
        return None

    # The full path should always be an absolute path starting with /
    # It is important it doesn't get misinterpreted as a scheme-relative URL (//host/path)
    full_path = '/' + full_path.lstrip('/')

    language = None
    version_slug = None
    schema, netloc, path, params, query, fragments = urlparse(full_path)
    if not project.single_version:
        language, version_slug, path = language_and_version_from_path(path)

    path, http_status = project.redirects.get_redirect_path_with_status(
        path=path, language=language, version_slug=version_slug
    )

    if path is None:
        return None

    new_path = urlunparse((schema, netloc, path, params, query, fragments))

    # Re-use the domain and protocol used in the current request.
    # Redirects shouldn't change the domain, version or language.
    # However, if the new_path is already an absolute URI, just use it
    new_path = request.build_absolute_uri(new_path)

    if http_status and http_status == 301:
        return HttpResponsePermanentRedirect(new_path)

    return HttpResponseRedirect(new_path)
