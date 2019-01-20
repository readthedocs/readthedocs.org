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

import itertools
import logging
import mimetypes
import os
from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import iri_to_uri
from django.views.decorators.cache import cache_page
from django.views.static import serve

from readthedocs.builds.models import Version
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.resolver import resolve, resolve_path
from readthedocs.core.symlink import PrivateSymlink, PublicSymlink
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ProjectRelationship
from readthedocs.projects.templatetags.projects_tags import sort_version_aware


log = logging.getLogger(__name__)


def map_subproject_slug(view_func):
    """
    A decorator that maps a ``subproject_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """

    @wraps(view_func)
    def inner_view(  # noqa
            request, subproject=None, subproject_slug=None, *args, **kwargs
    ):
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
    def inner_view(  # noqa
            request, project=None, project_slug=None, *args, **kwargs
    ):
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
    urlparse_result = urlparse(request.get_full_path())
    return HttpResponseRedirect(
        resolve(
            subproject or project,
            query_params=urlparse_result.query,
        )
    )


@map_project_slug
@map_subproject_slug
def redirect_page_with_filename(request, project, subproject, filename):  # pylint: disable=unused-argument  # noqa
    """Redirect /page/file.html to /en/latest/file.html."""
    urlparse_result = urlparse(request.get_full_path())
    return HttpResponseRedirect(
        resolve(
            subproject or project,
            filename=filename,
            query_params=urlparse_result.query,
        )
    )


def _serve_401(request, project):
    res = render(request, '401.html')
    res.status_code = 401
    log.debug('Unauthorized access to {} documentation'.format(project.slug))
    return res


def _serve_file(request, filename, basepath):
    """
    Serve media file via Django or NGINX based on ``PYTHON_MEDIA``.

    When using ``PYTHON_MEDIA=True`` (or when ``DEBUG=True``) the file is served
    by ``django.views.static.serve`` function.

    On the other hand, when ``PYTHON_MEDIA=False`` the file is served by using
    ``X-Accel-Redirect`` header for NGINX to take care of it and serve the file.

    :param request: Django HTTP request
    :param filename: path to the filename to be served relative to ``basepath``
    :param basepath: base path to prepend to the filename

    :returns: Django HTTP response object

    :raises: ``Http404`` on ``UnicodeEncodeError``
    """
    # Serve the file from the proper location
    if settings.DEBUG or getattr(settings, 'PYTHON_MEDIA', False):
        # Serve from Python
        return serve(request, filename, basepath)

    # Serve from Nginx
    content_type, encoding = mimetypes.guess_type(
        os.path.join(basepath, filename),
    )
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
        request,
        project,
        subproject,
        lang_slug=None,
        version_slug=None,
        filename='',
):
    """Map existing proj, lang, version, filename views to the file format."""
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
        'File not found. Tried these files: %s' % ','.join(files_tried),
    )


@map_project_slug
def robots_txt(request, project):
    """
    Serve custom user's defined ``/robots.txt``.

    If the user added a ``robots.txt`` in the "default version" of the project,
    we serve it directly.
    """
    # Use the ``robots.txt`` file from the default version configured
    version_slug = project.get_default_version()
    version = project.versions.get(slug=version_slug)

    no_serve_robots_txt = any([
        # If project is private or,
        project.privacy_level == constants.PRIVATE,
        # default version is private or,
        version.privacy_level == constants.PRIVATE,
        # default version is not active or,
        not version.active,
        # default version is not built
        not version.built,
    ])
    if no_serve_robots_txt:
        # ... we do return a 404
        raise Http404()

    filename = resolve_path(
        project,
        version_slug=version_slug,
        filename='robots.txt',
        subdomain=True,  # subdomain will make it a "full" path without a URL prefix
    )

    # This breaks path joining, by ignoring the root when given an "absolute" path
    if filename[0] == '/':
        filename = filename[1:]

    basepath = PublicSymlink(project).project_root
    fullpath = os.path.join(basepath, filename)

    if os.path.exists(fullpath):
        return HttpResponse(open(fullpath).read(), content_type='text/plain')

    return HttpResponse('User-agent: *\nAllow: /\n', content_type='text/plain')


@map_project_slug
# TODO: make this cache dependent on the project's slug
@cache_page(60 * 60 * 24 * 3)  # 3 days
def sitemap_xml(request, project):
    """
    Generate and serve a ``sitemap.xml`` for a particular ``project``.

    The sitemap is generated from all the ``active`` and public versions of
    ``project``. These versions are sorted by using semantic versioning
    prepending ``latest`` and ``stable`` (if they are enabled) at the beginning.

    Following this order, the versions are assigned priorities and change
    frequency. Starting from 1 and decreasing by 0.1 for priorities and starting
    from daily, weekly to monthly for change frequency.

    If the project is private, the view raises ``Http404``. On the other hand,
    if the project is public but a version is private, this one is not included
    in the sitemap.

    :param request: Django request object
    :param project: Project instance to generate the sitemap

    :returns: response with the ``sitemap.xml`` template rendered

    :rtype: django.http.HttpResponse
    """
    def priorities_generator():
        """
        Generator returning ``priority`` needed by sitemap.xml.

        It generates values from 1 to 0.1 by decreasing in 0.1 on each
        iteration. After 0.1 is reached, it will keep returning 0.1.
        """
        priorities = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
        yield from itertools.chain(priorities, itertools.repeat(0.1))

    def changefreqs_generator():
        """
        Generator returning ``changefreq`` needed by sitemap.xml.

        It returns ``daily`` on first iteration, then ``weekly`` and then it
        will return always ``monthly``.

        We are using ``monthly`` as last value because ``never`` is too
        aggressive. If the tag is removed and a branch is created with the same
        name, we will want bots to revisit this.
        """
        changefreqs = ['daily', 'weekly']
        yield from itertools.chain(changefreqs, itertools.repeat('monthly'))

    if project.privacy_level == constants.PRIVATE:
        raise Http404

    sorted_versions = sort_version_aware(
        project.versions.filter(
            active=True,
            privacy_level=constants.PUBLIC,
        ),
    )

    versions = []
    for version, priority, changefreq in zip(
            sorted_versions, priorities_generator(), changefreqs_generator()):
        element = {
            'loc': version.get_subdomain_url(),
            'priority': priority,
            'changefreq': changefreq,
            'languages': [],
        }

        # Version can be enabled, but not ``built`` yet. We want to show the
        # link without a ``lastmod`` attribute
        last_build = version.builds.order_by('-date').first()
        if last_build:
            element['lastmod'] = last_build.date.isoformat()

        if project.translations.exists():
            for translation in project.translations.all():
                href = project.get_docs_url(
                    version_slug=version.slug,
                    lang_slug=translation.language,
                    private=version.privacy_level == constants.PRIVATE,
                )
                element['languages'].append({
                    'hreflang': translation.language,
                    'href': href,
                })

            # Add itself also as protocol requires
            element['languages'].append({
                'hreflang': project.language,
                'href': element['loc'],
            })

        versions.append(element)

    context = {
        'versions': versions,
    }
    return render(request, 'sitemap.xml', context, content_type='application/xml')
