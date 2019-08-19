import itertools
import logging
import mimetypes
import os
from functools import wraps
from urllib.parse import urlparse

from django.core.files.storage import get_storage_class
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import iri_to_uri
from django.views.decorators.cache import cache_page
from django.views.static import serve

from readthedocs.builds.constants import LATEST, STABLE
from readthedocs.builds.models import Version
from readthedocs.core.resolver import resolve, resolve_path
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ProjectRelationship
from readthedocs.projects.templatetags.projects_tags import sort_version_aware

log = logging.getLogger(__name__)


def _log(request, msg):
    log.info(f'(Proxito) {msg} [{request.get_host()}{request.get_full_path()}')


def _serve_401(request, project):
    res = render(request, '401.html')
    res.status_code = 401
    log.debug('Unauthorized access to %s documentation', project.slug)
    return res


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
            # Get a slug from the request if it can't be found in the URL
            if not project_slug:
                project_slug = request.host_project_slug
                log.debug(f'Inserting project slug from request [{project_slug}')
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise Http404('Project does not exist.')
        return view_func(request, project=project, *args, **kwargs)

    return inner_view


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
    """
    Take the incoming parsed URL's and figure out what file to serve.

    """
    # Take the most relvent project so far
    current_project = subproject or project

    # Handle a / redirect when we aren't a single version
    if lang_slug is None and version_slug is None and filename is '' and not current_project.single_version:
        urlparse_result = urlparse(request.get_full_path())
        _log(request, msg='Redirecting to default')

        return HttpResponseRedirect(
            resolve(
                subproject or project,
                query_params=urlparse_result.query,
            ),
        )

    # We actually want to serve a translation!
    if lang_slug and lang_slug != current_project.language:
        final_project = get_object_or_404(current_project.translations.all(), language=lang_slug)
    else:
        final_project = current_project

    # Handle redirects
    # path, http_status = final_project.redirects.get_redirect_path_with_status(
    #     language=lang_slug, version_slug=version_slug, path=filename
    # )

    # final_project is now the actual project we want to serve docs on,
    # accounting for the main Project, Subproject, and Translations of such

    # Single Version project
    if not version_slug:
        version_slug = final_project.get_default_version()
    try:
        (
            Version.objects
            .public(user=request.user, project=final_project)
            .get(slug=version_slug)
        )
    except Version.DoesNotExist:
        # Properly raise a 404 if the version doesn't exist (or is inactive) and
        # a 401 if it does
        if final_project.versions.filter(slug=version_slug, active=True).exists():
            return _serve_401(request, final_project)
        raise Http404('Version does not exist.')

    storage_path = final_project.get_storage_path(
        type_='html', version_slug=version_slug, include_file=False
    )

    path = f'{storage_path}/{filename}'
    if path[-1] == '/':
        path += 'index.html'

    # Serve from the filesystem if using DEBUG or Testing
    # Tests require this now since we don't want to check for the file existing in prod
    if settings.DEBUG or settings.TEST:
        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        root_path = storage.path('')
        # Serve from Python
        return serve(request, path, root_path)

    # Serve via nginx
    return _serve_docs_nginx(
        request,
        final_project=final_project,
        path=f'/proxito/{path}'
    )


def _serve_docs_nginx(request, final_project, path):

    log.info('Serving %s for %s', path, final_project)

    # Serve from Nginx
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(content_type=content_type)
    if encoding:
        response['Content-Encoding'] = encoding
    try:
        # NGINX does not support non-ASCII characters in the header, so we
        # convert the IRI path to URI so it's compatible with what NGINX expects
        # as the header value.
        # https://github.com/benoitc/gunicorn/issues/1448
        # https://docs.djangoproject.com/en/1.11/ref/unicode/#uri-and-iri-handling
        x_accel_redirect = iri_to_uri(path)
        response['X-Accel-Redirect'] = x_accel_redirect
    except UnicodeEncodeError:
        log.exception('Unicode Error in serve_docs function')
        raise Http404

    return response


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

    sitemap_url = '{scheme}://{domain}/sitemap.xml'.format(
        scheme='https',
        domain=project.subdomain(),
    )
    return HttpResponse(
        'User-agent: *\nAllow: /\nSitemap: {}\n'.format(sitemap_url),
        content_type='text/plain',
    )


@map_project_slug
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

    def hreflang_formatter(lang):
        """
        sitemap hreflang should follow correct format.

        Use hyphen instead of underscore in language and country value.
        ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
        """
        if '_' in lang:
            return lang.replace("_", "-")
        return lang

    def changefreqs_generator():
        """
        Generator returning ``changefreq`` needed by sitemap.xml.

        It returns ``weekly`` on first iteration, then ``daily`` and then it
        will return always ``monthly``.

        We are using ``monthly`` as last value because ``never`` is too
        aggressive. If the tag is removed and a branch is created with the same
        name, we will want bots to revisit this.
        """
        changefreqs = ['weekly', 'daily']
        yield from itertools.chain(changefreqs, itertools.repeat('monthly'))

    if project.privacy_level == constants.PRIVATE:
        raise Http404

    sorted_versions = sort_version_aware(
        Version.internal.public(
            project=project,
            only_active=True,
        ),
    )

    # This is a hack to swap the latest version with
    # stable version to get the stable version first in the sitemap.
    # We want stable with priority=1 and changefreq='weekly' and
    # latest with priority=0.9 and changefreq='daily'
    # More details on this: https://github.com/rtfd/readthedocs.org/issues/5447
    if (
        len(sorted_versions) >= 2 and
        sorted_versions[0].slug == LATEST and
        sorted_versions[1].slug == STABLE
    ):
        sorted_versions[0], sorted_versions[1] = sorted_versions[1], sorted_versions[0]

    versions = []
    for version, priority, changefreq in zip(
            sorted_versions,
            priorities_generator(),
            changefreqs_generator(),
    ):
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
                translation_versions = (
                    Version.internal.public(project=translation)
                    .values_list('slug', flat=True)
                )
                if version.slug in translation_versions:
                    href = project.get_docs_url(
                        version_slug=version.slug,
                        lang_slug=translation.language,
                        private=False,
                    )
                    element['languages'].append({
                        'hreflang': hreflang_formatter(translation.language),
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
    return render(
        request,
        'sitemap.xml',
        context,
        content_type='application/xml',
    )
