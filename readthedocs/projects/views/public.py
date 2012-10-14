import simplejson

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import (HttpResponse, HttpResponseRedirect,
                         Http404, HttpResponsePermanentRedirect)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from django.utils.datastructures import SortedDict

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import get_objects_for_user
from taggit.models import Tag

from core.views import serve_docs
from projects.models import Project
from projects.utils import highest_version


def project_index(request, username=None, tag=None):
    """
    The list of projects, which will optionally filter by user or tag,
    in which case a 'person' or 'tag' will be added to the context
    """
    queryset = Project.objects.public(request.user)
    if username:
        user = get_object_or_404(User, username=username)
        queryset = queryset.filter(user=user)
    else:
        user = None

    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(tags__name__in=[tag.slug])
    else:
        tag = None

    return object_list(
        request,
        queryset=queryset,
        extra_context={'person': user, 'tag': tag},
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
    )


def project_detail(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    versions = project.versions.public(request.user, project)
    return render_to_response(
        'projects/project_detail.html',
        {
            'project': project,
            'versions': versions,
        },
        context_instance=RequestContext(request),
    )

def project_downloads(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    project = get_object_or_404(Project.objects.protected(request.user), slug=project_slug)
    versions = project.ordered_active_versions()
    version_data = SortedDict()
    for version in versions:
        version_data[version.slug] = {}
        if project.has_pdf(version.slug):
            version_data[version.slug]['pdf_url'] = project.get_pdf_url(version.slug)
        if project.has_htmlzip(version.slug):
            version_data[version.slug]['htmlzip_url'] = project.get_htmlzip_url(version.slug)
        if project.has_epub(version.slug):
            version_data[version.slug]['epub_url'] = project.get_epub_url(version.slug)
        if project.has_manpage(version.slug):
            version_data[version.slug]['manpage_url'] = project.get_manpage_url(version.slug)
        #Kill ones that have no downloads.
        if not len(version_data[version.slug]):
            del version_data[version.slug]
    return render_to_response(
        'projects/project_downloads.html',
        {
            'project': project,
            'version_data': version_data,
            'versions': versions,
        },
        context_instance=RequestContext(request),
    )


def legacy_project_detail(request, username, project_slug):
    return HttpResponsePermanentRedirect(reverse(
        project_detail, kwargs = {
            'project_slug': project_slug,
        }
    ))

def tag_index(request):
    """
    List of all tags by most common
    """
    tag_qs = Project.tags.most_common()
    return object_list(
        request,
        queryset=tag_qs,
        page=int(request.GET.get('page', 1)),
        template_object_name='tag',
        template_name='projects/tag_list.html',
    )

def search(request):
    """
    our ghetto site search.  see roadmap.
    """
    if 'q' in request.GET:
        term = request.GET['q']
    else:
        raise Http404
    queryset = Project.objects.live(name__icontains=term)
    if queryset.count() == 1:
        return HttpResponseRedirect(queryset[0].get_absolute_url())

    return object_list(
        request,
        queryset=queryset,
        template_object_name='term',
        extra_context={'term': term},
        template_name='projects/search.html',
    )

def search_autocomplete(request):
    """
    return a json list of project names
    """
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    queryset = Project.objects.live(name__icontains=term)[:20]

    project_names = queryset.values_list('name', flat=True)
    json_response = simplejson.dumps(list(project_names))

    return HttpResponse(json_response, mimetype='text/javascript')


def subdomain_handler(request, lang_slug=None, version_slug=None, filename=''):
    """
    This provides the fall-back routing for subdomain requests.

    This was made primarily to redirect old subdomain's to their version'd brothers.
    """
    project = get_object_or_404(Project, slug=request.slug)
    # Don't add index.html for htmldir.
    if not filename and project.documentation_type != 'sphinx_htmldir':
        filename = "index.html"
    if version_slug is None:
        #Handle / on subdomain.
        default_version = project.get_default_version()
        url = reverse(serve_docs, kwargs={
            'version_slug': default_version,
            'lang_slug': 'en',
            'filename': filename
        })
        return HttpResponseRedirect(url)
    if version_slug and lang_slug is None:
        #Handle /version/ on subdomain.
        aliases = project.aliases.filter(from_slug=version_slug)
        #Handle Aliases.
        if aliases.count():
            if aliases[0].largest:
                highest_ver = highest_version(project.versions.filter(slug__contains=version_slug, active=True))
                version_slug = highest_ver[0].slug
            else:
                version_slug = aliases[0].to_slug
            url = reverse(serve_docs, kwargs={
                'version_slug': version_slug,
                'lang_slug': 'en',
                'filename': filename
            })
        else:
            try:
                url = reverse(serve_docs, kwargs={
                    'version_slug': version_slug,
                    'lang_slug': 'en',
                    'filename': filename
                })
            except NoReverseMatch:
                raise Http404
        return HttpResponseRedirect(url)
    return serve_docs(request=request,
                      project_slug=project.slug,
                      lang_slug=lang_slug,
                      version_slug=version_slug,
                      filename=filename)
