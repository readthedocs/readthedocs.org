import logging
import mimetypes
from functools import wraps
from urllib.parse import urlparse

from django.core.files.storage import get_storage_class
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import iri_to_uri
from django.views.static import serve

from readthedocs.projects.models import Project, ProjectRelationship

log = logging.getLogger(__name__)


def _log(request, msg):
    log.info(f'(Proxito) {msg} [{request.get_host()}{request.get_full_path()}')


def _serve_401(request, project):
    res = render(request, '401.html')
    res.status_code = 401
    log.debug('Unauthorized access to %s documentation', project.slug)
    return res


def _fallback():
    res = HttpResponse('Internal fallback to RTD app')
    res.status_code = 420
    log.debug('Falling back to RTD app')
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
                log.debug(f'Inserting project slug from request [{project_slug}]')
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
    # Take the most relevant project so far
    current_project = subproject or project

    # Handle a / redirect when we aren't a single version
    if lang_slug is None and version_slug is None and filename is '' and not current_project.single_version:
        _log(request, msg='Redirecting to default')
        return _fallback()


    # Check to see if we need to serve a translation
    if lang_slug and lang_slug == current_project.language:
        final_project = current_project
    else:
        final_project = get_object_or_404(current_project.translations.all(), language=lang_slug)

    # final_project is now the actual project we want to serve docs on,
    # accounting for:
    # * Project
    # * Subproject
    # * Translations

    # TODO: Redirects need to be refactored before we can turn them on
    # They currently do 1 request per redirect that exists for the project
    # path, http_status = final_project.redirects.get_redirect_path_with_status(
    #     language=lang_slug, version_slug=version_slug, path=filename
    # )

    if not version_slug:
        version_slug = final_project.get_default_version()

    # Don't do auth checks
    # try:
    #     Version.objects.public(user=request.user, project=final_project).get(slug=version_slug)
    # except Version.DoesNotExist:
    #     # Properly raise a 404 if the version doesn't exist (or is inactive) and
    #     # a 401 if it does
    #     if final_project.versions.filter(slug=version_slug, active=True).exists():
    #         return _serve_401(request, final_project)
    #     raise Http404('Version does not exist.')

    storage_path = final_project.get_storage_path(
        type_='html', version_slug=version_slug, include_file=False
    )

    path = f'{storage_path}/{filename}'
    if path[-1] == '/':
        path += 'index.html'

    # Serve from the filesystem if using DEBUG or Testing
    # Tests require this now since we don't want to check for the file existing in prod
    if settings.DEBUG:
        log.info('[Django serve] %s for %s', path, final_project)
        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        root_path = storage.path('')
        # Serve from Python
        return serve(request, path, root_path)

    # Serve via nginx
    log.info('[Nginx serve] %s for %s', path, final_project)
    return _serve_docs_nginx(
        request,
        final_project=final_project,
        path=f'/proxito/{path}'
    )


def _serve_docs_nginx(request, final_project, path):

    # Serve from Nginx
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(f'Serving internal path: {path}', content_type=content_type)
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
