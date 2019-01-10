# -*- coding: utf-8 -*-
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

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import mimetypes
import os
from functools import wraps

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.static import serve

from readthedocs.builds.models import Version
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.resolver import resolve, resolve_path
from readthedocs.core.symlink import PrivateSymlink, PublicSymlink
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ProjectRelationship

log = logging.getLogger(__name__)


def map_subproject_slug(view_func):
    """
    A decorator that maps a ``subproject_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """
    @wraps(view_func)
    def inner_view(request, subproject=None, subproject_slug=None, *args, **kwargs):  # noqa
        if subproject is None and subproject_slug:
            # Try to fetch by subproject alias first, otherwise we might end up
            # redirected to an unrelated project.
            try:
                # Depends on a project passed into kwargs
                rel = ProjectRelationship.objects.get(
                    parent=kwargs['project'],
                    alias=subproject_slug,
                )
                subproject = rel.child
            except (ProjectRelationship.DoesNotExist, KeyError):
                subproject = get_object_or_404(Project, slug=subproject_slug)
        return view_func(request, subproject=subproject, *args, **kwargs)

    return inner_view


def map_project_slug(view_func):
    """
    A decorator that maps a ``project_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """
    @wraps(view_func)
    def inner_view(request, project=None, project_slug=None, *args, **kwargs):  # noqa
        if project is None:
            if not project_slug:
                project_slug = request.slug
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise Http404('Project does not exist.')
        return view_func(request, project=project, *args, **kwargs)

    return inner_view


@map_project_slug
@map_subproject_slug
def redirect_project_slug(request, project, subproject):  # pylint: disable=unused-argument
    """Handle / -> /en/latest/ directs on subdomains."""
    return HttpResponseRedirect(resolve(subproject or project))


@map_project_slug
@map_subproject_slug
def redirect_page_with_filename(request, project, subproject, filename):  # pylint: disable=unused-argument  # noqa
    """Redirect /page/file.html to /en/latest/file.html."""
    return HttpResponseRedirect(
        resolve(subproject or project, filename=filename))


def _serve_401(request, project):
    res = render(request, '401.html')
    res.status_code = 401
    log.debug('Unauthorized access to {0} documentation'.format(project.slug))
    return res


def _serve_file(request, filename, basepath):
    # Serve the file from the proper location
    if settings.DEBUG or getattr(settings, 'PYTHON_MEDIA', False):
        # Serve from Python
        return serve(request, filename, basepath)

    # Serve from Nginx
    content_type, encoding = mimetypes.guess_type(
        os.path.join(basepath, filename))
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(content_type=content_type)
    if encoding:
        response['Content-Encoding'] = encoding
    try:
        iri_path = os.path.join(
            basepath[len(settings.SITE_ROOT):],
            filename,
        )
        # NGINX does not support non-ASCII characters in the header, so we
        # convert the IRI path to URI so it's compatible with what NGINX expects
        # as the header value.
        # https://github.com/benoitc/gunicorn/issues/1448
        # https://docs.djangoproject.com/en/1.11/ref/unicode/#uri-and-iri-handling
        x_accel_redirect = iri_to_uri(iri_path)
        response['X-Accel-Redirect'] = x_accel_redirect
    except UnicodeEncodeError:
        raise Http404

    return response


@map_project_slug
@map_subproject_slug
def serve_docs(
        request, project, subproject, lang_slug=None, version_slug=None,
        filename=''):
    """Exists to map existing proj, lang, version, filename views to the file format."""
    if not version_slug:
        version_slug = project.get_default_version()
    try:
        version = project.versions.public(request.user).get(slug=version_slug)
    except Version.DoesNotExist:
        # Properly raise a 404 if the version doesn't exist (or is inactive) and
        # a 401 if it does
        if project.versions.filter(slug=version_slug, active=True).exists():
            return _serve_401(request, project)
        raise Http404('Version does not exist.')
    filename = resolve_path(
        subproject or project,  # Resolve the subproject if it exists
        version_slug=version_slug,
        language=lang_slug,
        filename=filename,
        subdomain=True,  # subdomain will make it a "full" path without a URL prefix
    )
    if (version.privacy_level == constants.PRIVATE and
            not AdminPermission.is_member(user=request.user, obj=project)):
        return _serve_401(request, project)
    return _serve_symlink_docs(
        request,
        filename=filename,
        project=project,
        privacy_level=version.privacy_level,
    )


@map_project_slug
def _serve_symlink_docs(request, project, privacy_level, filename=''):
    """Serve a file by symlink, or a 404 if not found."""
    # Handle indexes
    if filename == '' or filename[-1] == '/':
        filename += 'index.html'

    # This breaks path joining, by ignoring the root when given an "absolute" path
    if filename[0] == '/':
        filename = filename[1:]

    log.info('Serving %s for %s', filename, project)

    files_tried = []

    serve_docs = getattr(settings, 'SERVE_DOCS', [constants.PRIVATE])

    if (settings.DEBUG or constants.PUBLIC in serve_docs) and privacy_level != constants.PRIVATE:  # yapf: disable  # noqa
        public_symlink = PublicSymlink(project)
        basepath = public_symlink.project_root
        if os.path.exists(os.path.join(basepath, filename)):
            return _serve_file(request, filename, basepath)

        files_tried.append(os.path.join(basepath, filename))

    if (settings.DEBUG or constants.PRIVATE in serve_docs) and privacy_level == constants.PRIVATE:  # yapf: disable  # noqa
        # Handle private
        private_symlink = PrivateSymlink(project)
        basepath = private_symlink.project_root

        if os.path.exists(os.path.join(basepath, filename)):
            return _serve_file(request, filename, basepath)

        files_tried.append(os.path.join(basepath, filename))

    raise Http404(
        'File not found. Tried these files: %s' % ','.join(files_tried))
