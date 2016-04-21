from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.static import serve

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.core.symlink import PublicSymlink
from readthedocs.core.resolver import resolve, resolve_path

import mimetypes
import os
import logging

log = logging.getLogger(__name__)


def map_project_slug(view_func):
    def inner_view(request, project_slug=None, *args, **kwargs):
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
    return HttpResponseRedirect(project.get_docs_url())


@map_project_slug
def redirect_page_with_filename(request, project, filename):
    """Redirect /page/file.html to /en/latest/file.html."""
    return HttpResponseRedirect(resolve(project, filename=filename))


@map_project_slug
def serve_docs(request, project, lang_slug, version_slug, filename):
    try:
        ver = Version.objects.public(request.user).get(
            project=project, slug=version_slug)
    except (Version.DoesNotExist):
        raise Http404

    if ver not in project.versions.public(request.user, project, only_active=False):
        r = render_to_response('401.html',
                               context_instance=RequestContext(request))
        r.status_code = 401
        return r
    filename = resolve_path(
        project, version_slug=version_slug, language=lang_slug, filename=filename
    )
    return serve_symlink_docs(request, filename, project_slug=project.slug)


@map_project_slug
def serve_symlink_docs(request, project, filename=''):
    # Handle indexes
    if filename == '' or filename[-1] == '/':
        filename += 'index.html'
    public_symlink = PublicSymlink(project)
    basepath = public_symlink.project_root
    log.info('Serving %s for %s' % (filename, project))

    if not settings.DEBUG and not getattr(settings, 'PYTHON_MEDIA', False):
        fullpath = os.path.join(basepath, filename)
        content_type, encoding = mimetypes.guess_type(fullpath)
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(content_type=content_type)
        if encoding:
            response["Content-Encoding"] = encoding
        try:
            response['X-Accel-Redirect'] = os.path.join(basepath[len(settings.SITE_ROOT):],
                                                        filename)
        except UnicodeEncodeError:
            raise Http404

        return response
    else:
        return serve(request, filename, basepath)
