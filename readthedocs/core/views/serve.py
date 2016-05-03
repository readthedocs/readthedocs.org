"""
Doc serving from Python.

In production there are two modes,
* Serving from public symlinks in nginx (readthedocs.org & readthedocs.com)
* Serving from private symlinks in Python (readthedocs.com only)

In development, we have two modes:
* Serving from public symlinks in Python
* Serving from private symlinks in Python

This means we should only serve from public symlinks in dev,
and generally default to serving from private symlinks in Python only.

Privacy
-------

These views will take into account the version privacy level.

Settings
--------

PYTHON_MEDIA (False) - Set this to True to serve docs & media from Python
SERVE_DOCS (['private']) - The list of ['private', 'public'] docs to serve.
"""

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.static import serve

from readthedocs.projects import constants
from readthedocs.projects.models import Project
from readthedocs.core.symlink import PrivateSymlink, PublicSymlink
from readthedocs.core.resolver import resolve, resolve_path
from readthedocs.privacy.loader import AdminPermission

import mimetypes
import os
import logging
from functools import wraps

log = logging.getLogger(__name__)


def map_project_slug(view_func):
    """
    A decorator that maps a ``project_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """
    @wraps(view_func)
    def inner_view(request, project=None, project_slug=None, *args, **kwargs):
        if project is None:
            if not project_slug:
                project_slug = request.slug
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise Http404
        return view_func(request, project=project, *args, **kwargs)
    return inner_view


@map_project_slug
def redirect_project_slug(request, project):
    """Handle / -> /en/latest/ directs on subdomains"""
    return HttpResponseRedirect(resolve(project))


@map_project_slug
def redirect_page_with_filename(request, project, filename):
    """Redirect /page/file.html to /en/latest/file.html."""
    return HttpResponseRedirect(resolve(project, filename=filename))


@map_project_slug
def serve_docs(request, project, lang_slug=None, version_slug=None, filename=''):
    """
    This exists mainly to map existing proj, lang, version, filename views to the file format.
    """
    filename = resolve_path(
        project, version_slug=version_slug, language=lang_slug, filename=filename
    )
    return serve_symlink_docs(request, filename=filename, project=project)


def _serve_file(request, filename, basepath):
    # Serve the file from the proper location
    if settings.DEBUG or getattr(settings, 'PYTHON_MEDIA', False):
        # Serve from Python
        return serve(request, filename, basepath)
    else:
        # Serve from Nginx
        content_type, encoding = mimetypes.guess_type(os.path.join(basepath, filename))
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(content_type=content_type)
        if encoding:
            response["Content-Encoding"] = encoding
        try:
            response['X-Accel-Redirect'] = os.path.join(
                basepath[len(settings.SITE_ROOT):],
                filename
            )
        except UnicodeEncodeError:
            raise Http404

        return response


def _serve_401(request, project):
    res = render_to_response('401.html',
                             context_instance=RequestContext(request))
    res.status_code = 401
    log.error('Unauthorized access to {0} documentation'.format(project.slug))
    return res


@map_project_slug
def serve_symlink_docs(request, project, filename=''):

    # Handle indexes
    if filename == '' or filename[-1] == '/':
        filename += 'index.html'

    # This breaks path joining, by ignoring the root when given an "absolute" path
    if filename[0] == '/':
        filename = filename[1:]

    log.info('Serving %s for %s' % (filename, project))

    files_tried = []

    serve_docs = getattr(settings, 'SERVE_DOCS', [constants.PRIVATE])

    if settings.DEBUG or constants.PUBLIC in serve_docs:
        public_symlink = PublicSymlink(project)
        basepath = public_symlink.project_root
        if os.path.exists(os.path.join(basepath, filename)):
            return _serve_file(request, filename, basepath)
        else:
            files_tried.append(os.path.join(basepath, filename))

    if settings.DEBUG or constants.PRIVATE in serve_docs:

        # Handle private
        private_symlink = PrivateSymlink(project)
        basepath = private_symlink.project_root

        if os.path.exists(os.path.join(basepath, filename)):

            # Do basic auth check on the project, but not the version
            if not AdminPermission.is_member(user=request.user, project=project):
                return _serve_401(request, project)

            return _serve_file(request, filename, basepath)
        else:
            files_tried.append(os.path.join(basepath, filename))

    raise Http404('File not found. Tried these files: %s' % ','.join(files_tried))
