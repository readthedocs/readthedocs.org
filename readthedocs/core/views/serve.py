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
SERVE_PUBLIC_DOCS (False) - Set this to True to serve public as well as private docs from Python
"""

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.static import serve

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, ProjectRelationship


import mimetypes
import os
import logging

log = logging.getLogger(__name__)


def subproject_list(request):
    project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)
    subprojects = [rel.child for rel in proj.subprojects.all()]
    return render_to_response(
        'projects/project_list.html',
        {'project_list': subprojects},
        context_instance=RequestContext(request)
    )


def subproject_serve_docs(request, project_slug, lang_slug=None,
                          version_slug=None, filename=''):
    parent_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)
    subproject_qs = ProjectRelationship.objects.filter(
        parent__slug=parent_slug, child__slug=project_slug)
    if lang_slug is None or version_slug is None:
        # Handle /
        version_slug = proj.get_default_version()
        url = reverse('subproject_docs_detail', kwargs={
            'project_slug': project_slug,
            'version_slug': version_slug,
            'lang_slug': proj.language,
            'filename': filename
        })
        return HttpResponseRedirect(url)

    if subproject_qs.exists():
        return serve_docs(request, lang_slug, version_slug, filename,
                          project_slug)
    else:
        log.info('Subproject lookup failed: %s:%s' % (project_slug,
                                                      parent_slug))
        raise Http404("Subproject does not exist")


def default_docs_kwargs(request, project_slug=None):
    """
    Return kwargs used to reverse lookup a project's default docs URL.

    Determining which URL to redirect to is done based on the kwargs
    passed to reverse(serve_docs, kwargs).  This function populates
    kwargs for the default docs for a project, and sets appropriate keys
    depending on whether request is for a subdomain URL, or a non-subdomain
    URL.

    """
    if project_slug:
        try:
            proj = Project.objects.get(slug=project_slug)
        except (Project.DoesNotExist, ValueError):
            # Try with underscore, for legacy
            try:
                proj = Project.objects.get(slug=project_slug.replace('-', '_'))
            except (Project.DoesNotExist):
                proj = None
    else:
        # If project_slug isn't in URL pattern, it's set in subdomain
        # middleware as request.slug.
        try:
            proj = Project.objects.get(slug=request.slug)
        except (Project.DoesNotExist, ValueError):
            # Try with underscore, for legacy
            try:
                proj = Project.objects.get(slug=request.slug.replace('-', '_'))
            except (Project.DoesNotExist):
                proj = None
    if not proj:
        raise Http404("Project slug not found")
    version_slug = proj.get_default_version()
    kwargs = {
        'project_slug': project_slug,
        'version_slug': version_slug,
        'lang_slug': proj.language,
        'filename': ''
    }
    # Don't include project_slug for subdomains.
    # That's how reverse(serve_docs, ...) differentiates subdomain
    # views from non-subdomain views.
    if project_slug is None:
        del kwargs['project_slug']
    return kwargs


def redirect_lang_slug(request, lang_slug, project_slug=None):
    """Redirect /en/ to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['lang_slug'] = lang_slug
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_version_slug(request, version_slug, project_slug=None):
    """Redirect /latest/ to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['version_slug'] = version_slug
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_project_slug(request, project_slug=None):
    """Redirect / to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_page_with_filename(request, filename, project_slug=None):
    """Redirect /page/file.html to /en/latest/file.html."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['filename'] = filename
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def serve_docs(request, lang_slug, version_slug, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    try:
        proj = Project.objects.protected(request.user).get(slug=project_slug)
        ver = Version.objects.public(request.user).get(
            project__slug=project_slug, slug=version_slug)
    except (Project.DoesNotExist, Version.DoesNotExist):
        proj = None
        ver = None
    if not proj or not ver:
        return server_helpful_404(request, project_slug, lang_slug, version_slug,
                                  filename)

    if ver not in proj.versions.public(request.user, proj, only_active=False):
        r = render_to_response('401.html',
                               context_instance=RequestContext(request))
        r.status_code = 401
        return r
    return _serve_docs(request, project=proj, version=ver, filename=filename,
                       lang_slug=lang_slug, version_slug=version_slug,
                       project_slug=project_slug)


def _serve_docs(request, project, version, filename, lang_slug=None,
                version_slug=None, project_slug=None):
    '''Actually serve the built documentation files

    This is not called directly, but is wrapped by :py:func:`serve_docs` so that
    authentication can be manipulated.
    '''
    # Figure out actual file to serve
    if not filename:
        filename = "index.html"
    # This is required because we're forming the filenames outselves instead of
    # letting the web server do it.
    elif (
            (project.documentation_type == 'sphinx_htmldir' or
             project.documentation_type == 'mkdocs') and
            "_static" not in filename and
            ".css" not in filename and
            ".js" not in filename and
            ".png" not in filename and
            ".jpg" not in filename and
            ".svg" not in filename and
            "_images" not in filename and
            ".html" not in filename and
            "font" not in filename and
            "inv" not in filename):
        filename += "index.html"
    else:
        filename = filename.rstrip('/')
    # Use the old paths if we're on our old location.
    # Otherwise use the new language symlinks.
    # This can be removed once we have 'en' symlinks for every project.
    if lang_slug == project.language:
        basepath = project.rtd_build_path(version_slug)
    else:
        basepath = project.translations_symlink_path(lang_slug)
        basepath = os.path.join(basepath, version_slug)

    # Serve file
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


def serve_single_version_docs(request, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)

    # This function only handles single version projects
    if not proj.single_version:
        raise Http404

    return serve_docs(request, proj.language, proj.default_version,
                      filename, project_slug)
