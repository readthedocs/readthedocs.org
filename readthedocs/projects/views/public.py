import json

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from core.generic.list_detail import object_list
from django.utils.datastructures import SortedDict

from taggit.models import Tag

from builds.filters import VersionSlugFilter
from builds.models import Version
from projects.models import Project


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
    filter = VersionSlugFilter(request.GET, queryset=versions)
    return render_to_response(
        'projects/project_detail.html',
        {
            'project': project,
            'versions': versions,
            'filter': filter,
        },
        context_instance=RequestContext(request),
    )


def project_downloads(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    versions = project.ordered_active_versions()
    version_data = SortedDict()
    for version in versions:
        data = version.get_downloads()
        # Don't show ones that have no downloads.
        if data:
            version_data[version.slug] = data

    # in case the MEDIA_URL is a protocol relative URL we just assume
    # we want http as the protcol, so that Dash is able to handle the URL
    if settings.MEDIA_URL.startswith('//'):
        media_url_prefix = u'http:'
    # but in case we're in debug mode and the MEDIA_URL is just a path
    # we prefix it with a hardcoded host name and protocol
    elif settings.MEDIA_URL.startswith('/') and settings.DEBUG:
        media_url_prefix = u'http://%s' % request.get_host()
    else:
        media_url_prefix = ''
    return render_to_response(
        'projects/project_downloads.html',
        {
            'project': project,
            'version_data': version_data,
            'versions': versions,
            'media_url_prefix': media_url_prefix,
        },
        context_instance=RequestContext(request),
    )


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
    queryset = (Project.objects.public(request.user)
                .filter(name__icontains=term)[:20])

    project_names = queryset.values_list('name', flat=True)
    json_response = json.dumps(list(project_names))

    return HttpResponse(json_response, mimetype='text/javascript')


def version_autocomplete(request, project_slug):
    """
    return a json list of version names
    """
    queryset = Project.objects.protected(request.user)
    get_object_or_404(queryset, slug=project_slug)
    versions = Version.objects.public(request.user)
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    version_queryset = versions.filter(slug__icontains=term)[:20]

    names = version_queryset.values_list('slug', flat=True)
    json_response = json.dumps(list(names))

    return HttpResponse(json_response, mimetype='text/javascript')


def version_filter_autocomplete(request, project_slug):
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    versions = Version.objects.public(request.user)
    filter = VersionSlugFilter(request.GET, queryset=versions)
    format = request.GET.get('format', 'json')

    if format == 'json':
        names = filter.qs.values_list('slug', flat=True)
        json_response = json.dumps(list(names))
        return HttpResponse(json_response, mimetype='text/javascript')
    elif format == 'html':
        return render_to_response(
            'core/version_list.html',
            {
                'project': project,
                'versions': versions,
                'filter': filter,
            },
            context_instance=RequestContext(request),
        )
    else:
        raise HttpResponse(status=400)
