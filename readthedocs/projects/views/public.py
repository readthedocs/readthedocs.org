import collections
import operator
import os
import json
import logging
import mimetypes
import md5

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView, DetailView
from django.utils.datastructures import SortedDict
from django.views.decorators.cache import cache_page

from taggit.models import Tag
import requests

from .base import ProjectOnboardMixin
from builds.filters import VersionSlugFilter
from builds.models import Version
from projects.models import Project, ImportedFile
from search.indexes import PageIndex
from search.views import LOG_TEMPLATE

log = logging.getLogger(__name__)
search_log = logging.getLogger(__name__ + '.search')
mimetypes.add_type("application/epub+zip", ".epub")


class ProjectIndex(ListView):
    model = Project

    def get_queryset(self):
        queryset = Project.objects.public(self.request.user)

        if self.kwargs.get('tag'):
            self.tag = get_object_or_404(Tag, slug=self.kwargs.get('tag'))
            queryset = queryset.filter(tags__name__in=[self.tag.slug])
        else:
            self.tag = None

        if self.kwargs.get('username'):
            self.user = get_object_or_404(User, username=self.kwargs.get('username'))
            queryset = queryset.filter(user=self.user)
        else:
            self.user = None

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectIndex, self).get_context_data(**kwargs)
        context['person'] = self.user
        context['tag'] = self.tag
        return context

project_index = ProjectIndex.as_view()


class ProjectDetailView(ProjectOnboardMixin, DetailView):

    '''Display project onboard steps'''

    model = Project
    slug_url_kwarg = 'project_slug'

    def get_queryset(self):
        return Project.objects.protected(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)

        project = self.get_object()
        context['versions'] = Version.objects.public(
            user=self.request.user, project=project)
        context['filter'] = VersionSlugFilter(self.request.GET,
                                              queryset=context['versions'])

        protocol = 'http'
        if self.request.is_secure():
            protocol = 'https'

        context['badge_url'] = "%s://%s%s?version=%s" % (
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse('project_badge', args=[project.slug]),
            project.get_default_version(),
        )
        context['site_url'] = "%s://%s%s?badge=%s" % (
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse('projects_detail', args=[project.slug]),
            project.get_default_version(),
        )

        return context


def _badge_return(redirect, url):
    if redirect:
        return HttpResponseRedirect(url)
    else:
        response = requests.get(url)
        http_response = HttpResponse(response.content, mimetype="image/svg+xml")
        http_response['Cache-Control'] = 'no-cache'
        http_response['Etag'] = md5.new(url)
        return http_response


# TODO remove this, it's a temporary fix to heavy database usage
@cache_page(60 * 30)
def project_badge(request, project_slug, redirect=False):
    """
    Return a sweet badge for the project
    """
    version_slug = request.GET.get('version', 'latest')
    style = request.GET.get('style', 'flat')
    try:
        version = Version.objects.public(request.user).get(project__slug=project_slug, slug=version_slug)
    except Version.DoesNotExist:
        url = 'http://img.shields.io/badge/docs-unknown%20version-yellow.svg?style={style}'.format(style=style)
        return _badge_return(redirect, url)
    version_builds = version.builds.filter(type='html', state='finished').order_by('-date')
    if not version_builds.exists():
        url = 'http://img.shields.io/badge/docs-no%20builds-yellow.svg?style={style}'.format(style=style)
        return _badge_return(redirect, url)
    last_build = version_builds[0]
    if last_build.success:
        color = 'brightgreen'
    else:
        color = 'red'
    url = 'http://img.shields.io/badge/docs-%s-%s.svg?style=%s' % (version.slug.replace('-', '--'), color, style)
    return _badge_return(redirect, url)


def project_downloads(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    project = get_object_or_404(Project.objects.protected(request.user), slug=project_slug)
    versions = Version.objects.public(user=request.user, project=project)
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


def project_download_media(request, project_slug, type, version_slug):
    """
    Download a specific piece of media.
    Perform an auth check if serving in private mode.
    """
    # Do private project auth checks
    queryset = Project.objects.protected(request.user).filter(slug=project_slug)
    if not queryset.exists():
        raise Http404
    DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')
    if DEFAULT_PRIVACY_LEVEL == 'public' or settings.DEBUG:
        path = os.path.join(settings.MEDIA_URL, type, project_slug, version_slug,
                            '%s.%s' % (project_slug, type.replace('htmlzip', 'zip')))
        return HttpResponseRedirect(path)
    else:
        # Get relative media path
        path = queryset[0].get_production_media_path(type=type, version_slug=version_slug).replace(
            settings.PRODUCTION_ROOT, '/prod_artifacts'
        )
        mimetype, encoding = mimetypes.guess_type(path)
        mimetype = mimetype or 'application/octet-stream'
        response = HttpResponse(mimetype=mimetype)
        if encoding:
            response["Content-Encoding"] = encoding
        response['X-Accel-Redirect'] = path
        # Include version in filename; this fixes a long-standing bug
        filename = "%s-%s.%s" % (project_slug, version_slug, path.split('.')[-1])
        response['Content-Disposition'] = 'filename=%s' % filename
        return response


def search_autocomplete(request):
    """
    return a json list of project names
    """
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    queryset = (Project.objects.public(request.user).filter(name__icontains=term)[:20])

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
    queryset = Project.objects.public(request.user)
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
    queryset = Project.objects.public(request.user)
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
    if query:
        user = ''
        if request.user.is_authenticated():
            user = request.user
        log.info(LOG_TEMPLATE.format(
            user=user,
            project=project or '',
            type='inproject',
            version=version_slug or '',
            language='',
            msg=query or '',
        ))

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


def project_versions(request, project_slug):
    """
    Shows the available versions and lets the user choose which ones he would
    like to have built.
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)

    versions = Version.objects.public(user=request.user, project=project, only_active=False)
    active_versions = versions.filter(active=True)
    inactive_versions = versions.filter(active=False)
    inactive_filter = VersionSlugFilter(request.GET, queryset=inactive_versions)
    active_filter = VersionSlugFilter(request.GET, queryset=active_versions)

    return render_to_response(
        'projects/project_version_list.html',
        {
            'inactive_filter': inactive_filter,
            'active_filter': active_filter,
            'project': project,
        },
        context_instance=RequestContext(request)
    )


def project_analytics(request, project_slug):
    """
    Have a analytics API placeholder
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    analytics_cache = cache.get('analytics:%s' % project_slug)
    if analytics_cache:
        analytics = json.loads(analytics_cache)
    else:
        try:
            resp = requests.get(
                '{host}/api/v1/index/1/heatmap/'.format(host=settings.GROK_API_HOST),
                params={'project': project.slug, 'days': 7, 'compare': True}
            )
            analytics = resp.json()
            cache.set('analytics:%s' % project_slug, resp.content, 1800)
        except:
            analytics = None

    if analytics:
        page_list = list(reversed(sorted(analytics['page'].items(), key=operator.itemgetter(1))))
        version_list = list(reversed(sorted(analytics['version'].items(), key=operator.itemgetter(1))))
    else:
        page_list = []
        version_list = []

    full = request.GET.get('full')
    if not full:
        page_list = page_list[:20]
        version_list = version_list[:20]

    return render_to_response(
        'projects/project_analytics.html',
        {
            'project': project,
            'analytics': analytics,
            'page_list': page_list,
            'version_list': version_list,
            'full': full,
        },
        context_instance=RequestContext(request)
    )


def project_embed(request, project_slug):
    """
    Have a content API placeholder
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    version = project.versions.get(slug='latest')
    files = version.imported_files.order_by('path')

    return render_to_response(
        'projects/project_embed.html',
        {
            'project': project,
            'files': files,
            'settings': {
                'GROK_API_HOST': settings.GROK_API_HOST,
                'URI': request.build_absolute_uri(location='/').rstrip('/')
            }
        },
        context_instance=RequestContext(request)
    )
