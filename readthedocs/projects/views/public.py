import json
import logging

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView
from django.utils.datastructures import SortedDict

from taggit.models import Tag
import requests

from builds.filters import VersionSlugFilter
from builds.models import Version
from projects.models import Project, ImportedFile
from search.indexes import PageIndex

log = logging.getLogger(__name__)

class ProjectIndex(ListView):
    model = Project

    def get_queryset(self):
        queryset = Project.objects.public(self.request.user)
        if self.kwargs.get('username'):
            self.user = get_object_or_404(User, username=self.kwargs.get('username'))
            queryset = queryset.filter(user=self.user)
        else:
            self.user = None

        if self.kwargs.get('tag'):
            self.tag = get_object_or_404(Tag, slug=self.kwargs.get('tag'))
            queryset = queryset.filter(tags__name__in=[self.tag.slug])
        else:
            self.tag = None

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectIndex, self).get_context_data(**kwargs)
        context['person'] = self.user
        context['tag'] = self.tag
        return context

project_index = ProjectIndex.as_view()

def project_detail(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    versions = project.versions.public(request.user, project)
    filter = VersionSlugFilter(request.GET, queryset=versions)
    if request.is_secure():
        protocol = 'https'
    else:
        protocol = 'http'
    badge_url = "%s://%s%s?version=%s" % (
        protocol, 
        settings.PRODUCTION_DOMAIN,
        reverse('project_badge', args=[project.slug]),
        project.get_default_version(),
    )
    site_url = "%s://%s%s?badge=%s" % (
        protocol,
        settings.PRODUCTION_DOMAIN,
        reverse('projects_detail', args=[project.slug]),
        project.get_default_version(),
    )
    return render_to_response(
        'projects/project_detail.html',
        {
            'project': project,
            'versions': versions,
            'filter': filter,
            'badge_url': badge_url,
            'site_url': site_url,
        },
        context_instance=RequestContext(request),
    )

def _badge_return(redirect, url):
    if redirect:
        return HttpResponseRedirect(url)
    else:
        response = requests.get(url)
        return HttpResponse(response.content, mimetype="image/svg+xml")

def project_badge(request, project_slug, redirect=False):
    """
    Return a sweet badge for the project
    """
    version_slug = request.GET.get('version', 'latest')
    style = request.GET.get('style', '')
    try:
        version = Version.objects.get(project__slug=project_slug, slug=version_slug)
    except Version.DoesNotExist:
        url = 'http://img.shields.io/badge/Docs-Unknown%20Version-yellow.svg?style=' % style
        return _badge_return(redirect, url)
    version_builds = version.builds.filter(type='html', state='finished').order_by('-date')
    if not version_builds.exists():
        url = 'http://img.shields.io/badge/Docs-No%20Builds-yellow.svg%s' % style
        return _badge_return(redirect, url)
    last_build = version_builds[0]
    if last_build.success:
        color = 'green'
    else:
        color = 'red'
    url = 'http://img.shields.io/badge/Docs-%s-%s.svg?style=%s' % (version.slug.replace('-', '--'), color, style)
    return _badge_return(redirect, url)

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

    ret_list = []
    for project in queryset:
        ret_list.append({
            'label': project.name,
            'value': project.slug,
            })

    json_response = json.dumps(ret_list)
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


def file_autocomplete(request, project_slug):
    """
    return a json list of version names
    """
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    queryset = ImportedFile.objects.filter(project__slug=project_slug, path__icontains=term)[:20]

    ret_list = []
    for file in queryset:
        ret_list.append({
            'label': file.path,
            'value': file.path,
            })

    json_response = json.dumps(ret_list)
    return HttpResponse(json_response, mimetype='text/javascript')


def elastic_project_search(request, project_slug):
    """
    Use elastic search to search in a project.
    """
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    version_slug = request.GET.get('version', 'latest')
    query = request.GET.get('q', None)
    log.debug("(API Search) %s" % query)

    if query:

        kwargs = {}
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": query, "boost": 10}}},
                        {"match": {"headers": {"query": query, "boost": 5}}},
                        {"match": {"content": {"query": query}}},
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "headers": {},
                    "content": {},
                }
            },
            "fields": ["title", "project", "version", "path"],
            "filter": {
                "and": [
                    {"term": {"project": project_slug}},
                    {"term": {"version": version_slug}},
                ]
            },
            "size": 50  # TODO: Support pagination.
        }

        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

        results = PageIndex().search(body, **kwargs)
    else:
        results = {}

    if results:
        # pre and post 1.0 compat
        for num, hit in enumerate(results['hits']['hits']):
            for key, val in hit['fields'].items():
                if isinstance(val, list):
                    results['hits']['hits'][num]['fields'][key] = val[0]

    return render_to_response(
        'search/elastic_project_search.html',
        {
            'project': project,
            'query': query,
            'results': results,
        },
        context_instance=RequestContext(request),
    )

