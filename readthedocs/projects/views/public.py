"""Public project views"""

from __future__ import absolute_import
from collections import OrderedDict
import operator
import os
import json
import logging
import mimetypes

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, DetailView

from taggit.models import Tag
import requests

from .base import ProjectOnboardMixin
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, ImportedFile
from readthedocs.search.indexes import PageIndex
from readthedocs.search.views import LOG_TEMPLATE

log = logging.getLogger(__name__)
search_log = logging.getLogger(__name__ + '.search')
mimetypes.add_type("application/epub+zip", ".epub")


class ProjectIndex(ListView):

    """List view of public :py:class:`Project` instances"""

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

    """Display project onboard steps"""

    model = Project
    slug_url_kwarg = 'project_slug'

    def get_queryset(self):
        return Project.objects.protected(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)

        project = self.get_object()
        context['versions'] = Version.objects.public(
            user=self.request.user, project=project)

        protocol = 'http'
        if self.request.is_secure():
            protocol = 'https'

        version_slug = project.get_default_version()

        context['badge_url'] = "%s://%s%s?version=%s" % (
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse('project_badge', args=[project.slug]),
            project.get_default_version(),
        )
        context['site_url'] = "{url}?badge={version}".format(
            url=project.get_docs_url(version_slug),
            version=version_slug)

        return context


@never_cache
def project_badge(request, project_slug):
    """Return a sweet badge for the project"""
    version_slug = request.GET.get('version', LATEST)
    style = request.GET.get('style', 'flat')
    # Default to 24 hour cache lifetime
    max_age = request.GET.get('maxAge', 86400)
    try:
        version = Version.objects.public(request.user).get(
            project__slug=project_slug, slug=version_slug)
    except Version.DoesNotExist:
        url = (
            'https://img.shields.io/badge/docs-unknown%20version-yellow.svg'
            '?style={style}&maxAge={max_age}'
            .format(style=style, max_age=max_age))
        return HttpResponseRedirect(url)
    version_builds = version.builds.filter(type='html', state='finished').order_by('-date')
    if not version_builds.exists():
        url = (
            'https://img.shields.io/badge/docs-no%20builds-yellow.svg'
            '?style={style}&maxAge={max_age}'
            .format(style=style, max_age=max_age))
        return HttpResponseRedirect(url)
    last_build = version_builds[0]
    if last_build.success:
        color = 'brightgreen'
    else:
        color = 'red'
    url = (
        'https://img.shields.io/badge/docs-{version}-{color}.svg'
        '?style={style}&maxAge={max_age}'
        .format(version=version.slug.replace('-', '--'), color=color,
                style=style, max_age=max_age))
    return HttpResponseRedirect(url)


def project_downloads(request, project_slug):
    """A detail view for a project with various dataz"""
    project = get_object_or_404(Project.objects.protected(request.user), slug=project_slug)
    versions = Version.objects.public(user=request.user, project=project)
    version_data = OrderedDict()
    for version in versions:
        data = version.get_downloads()
        # Don't show ones that have no downloads.
        if data:
            version_data[version] = data

    return render_to_response(
        'projects/project_downloads.html',
        {
            'project': project,
            'version_data': version_data,
            'versions': versions,
        },
        context_instance=RequestContext(request),
    )


def project_download_media(request, project_slug, type_, version_slug):
    """
    Download a specific piece of media.

    Perform an auth check if serving in private mode.

    .. warning:: This is linked directly from the HTML pages.
                 It should only care about the Version permissions,
                 not the actual Project permissions.

    """
    version = get_object_or_404(
        Version.objects.public(user=request.user),
        project__slug=project_slug,
        slug=version_slug,
    )
    privacy_level = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')
    if privacy_level == 'public' or settings.DEBUG:
        path = os.path.join(settings.MEDIA_URL, type_, project_slug, version_slug,
                            '%s.%s' % (project_slug, type_.replace('htmlzip', 'zip')))
        return HttpResponseRedirect(path)
    else:
        # Get relative media path
        path = (version.project
                .get_production_media_path(
                    type_=type_, version_slug=version_slug)
                .replace(settings.PRODUCTION_ROOT, '/prod_artifacts'))
        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(content_type=content_type)
        if encoding:
            response["Content-Encoding"] = encoding
        response['X-Accel-Redirect'] = path
        # Include version in filename; this fixes a long-standing bug
        filename = "%s-%s.%s" % (project_slug, version_slug, path.split('.')[-1])
        response['Content-Disposition'] = 'filename=%s' % filename
        return response


def search_autocomplete(request):
    """Return a json list of project names"""
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
    return HttpResponse(json_response, content_type='text/javascript')


def version_autocomplete(request, project_slug):
    """Return a json list of version names"""
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

    return HttpResponse(json_response, content_type='text/javascript')


def version_filter_autocomplete(request, project_slug):
    queryset = Project.objects.public(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    versions = Version.objects.public(request.user)
    resp_format = request.GET.get('format', 'json')

    if resp_format == 'json':
        names = versions.values_list('slug', flat=True)
        json_response = json.dumps(list(names))
        return HttpResponse(json_response, content_type='text/javascript')
    elif resp_format == 'html':
        return render_to_response(
            'core/version_list.html',
            {
                'project': project,
                'versions': versions,
            },
            context_instance=RequestContext(request),
        )
    return HttpResponse(status=400)


def file_autocomplete(request, project_slug):
    """Return a json list of file names"""
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    queryset = ImportedFile.objects.filter(project__slug=project_slug, path__icontains=term)[:20]

    ret_list = []
    for filename in queryset:
        ret_list.append({
            'label': filename.path,
            'value': filename.path,
        })

    json_response = json.dumps(ret_list)
    return HttpResponse(json_response, content_type='text/javascript')


def elastic_project_search(request, project_slug):
    """Use elastic search to search in a project"""
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    version_slug = request.GET.get('version', LATEST)
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
            for key, val in list(hit['fields'].items()):
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
    """Project version list view

    Shows the available versions and lets the user choose which ones to build.
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)

    versions = Version.objects.public(user=request.user, project=project, only_active=False)
    active_versions = versions.filter(active=True)
    inactive_versions = versions.filter(active=False)

    # If there's a wiped query string, check the string against the versions
    # list and display a success message. Deleting directories doesn't know how
    # to fail.  :)
    wiped = request.GET.get('wipe', '')
    wiped_version = versions.filter(slug=wiped)
    if wiped and wiped_version.count():
        messages.success(request, 'Version wiped: ' + wiped)

    return render_to_response(
        'projects/project_version_list.html',
        {
            'inactive_versions': inactive_versions,
            'active_versions': active_versions,
            'project': project,
        },
        context_instance=RequestContext(request)
    )


def project_analytics(request, project_slug):
    """Have a analytics API placeholder"""
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
        except requests.exceptions.RequestException:
            analytics = None

    if analytics:
        page_list = list(reversed(sorted(list(analytics['page'].items()),
                                         key=operator.itemgetter(1))))
        version_list = list(reversed(sorted(list(analytics['version'].items()),
                                            key=operator.itemgetter(1))))
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
    """Have a content API placeholder"""
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    version = project.versions.get(slug=LATEST)
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
