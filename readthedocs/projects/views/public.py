"""Public project views."""

import json
import logging
import mimetypes
import operator
import os
from collections import OrderedDict

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import get_storage_class
from django.db.models import prefetch_related_objects
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView, ListView
from taggit.models import Tag

from readthedocs.analytics.tasks import analytics_event
from readthedocs.analytics.utils import get_client_ip
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.builds.views import BuildTriggerMixin
from readthedocs.projects.models import Project
from readthedocs.projects.templatetags.projects_tags import sort_version_aware

from .base import ProjectOnboardMixin


log = logging.getLogger(__name__)
search_log = logging.getLogger(__name__ + '.search')
mimetypes.add_type('application/epub+zip', '.epub')


class ProjectIndex(ListView):

    """List view of public :py:class:`Project` instances."""

    model = Project

    def get_queryset(self):
        queryset = Project.objects.public(self.request.user)
        queryset = queryset.exclude(users__profile__banned=True)

        if self.kwargs.get('tag'):
            self.tag = get_object_or_404(Tag, slug=self.kwargs.get('tag'))
            queryset = queryset.filter(tags__slug__in=[self.tag.slug])
        else:
            self.tag = None

        if self.kwargs.get('username'):
            self.user = get_object_or_404(
                User,
                username=self.kwargs.get('username'),
            )
            queryset = queryset.filter(user=self.user)
        else:
            self.user = None

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.user
        context['tag'] = self.tag
        return context


def project_redirect(request, invalid_project_slug):
    """
    Redirect project slugs that have underscores (``_``).

    Slugs with underscores are no longer allowed.
    Underscores are replaced by ``-`` and then redirected to that URL.
    """
    new_project_slug = invalid_project_slug.replace('_', '-')
    new_path = request.path.replace(invalid_project_slug, new_project_slug)
    return redirect('{}?{}'.format(
        new_path,
        request.GET.urlencode(),
    ))


class ProjectDetailView(BuildTriggerMixin, ProjectOnboardMixin, DetailView):

    """Display project onboard steps."""

    model = Project
    slug_url_kwarg = 'project_slug'

    def get_queryset(self):
        return Project.objects.protected(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.get_object()
        context['versions'] = self._get_versions(project)

        protocol = 'http'
        if self.request.is_secure():
            protocol = 'https'

        version_slug = project.get_default_version()

        context['badge_url'] = '{}://{}{}?version={}'.format(
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse('project_badge', args=[project.slug]),
            project.get_default_version(),
        )
        context['site_url'] = '{url}?badge={version}'.format(
            url=project.get_docs_url(version_slug),
            version=version_slug,
        )

        return context


@never_cache
def project_badge(request, project_slug):
    """Return a sweet badge for the project."""
    style = request.GET.get('style', 'flat')
    if style not in (
            'flat',
            'plastic',
            'flat-square',
            'for-the-badge',
            'social',
    ):
        style = 'flat'

    # Get the local path to the badge files
    badge_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'static',
        'projects',
        'badges',
        '%s-' + style + '.svg',
    )

    version_slug = request.GET.get('version', LATEST)
    file_path = badge_path % 'unknown'

    version = Version.objects.public(request.user).filter(
        project__slug=project_slug,
        slug=version_slug,
    ).first()

    if version:
        last_build = version.builds.filter(
            type='html',
            state='finished',
        ).order_by('-date').first()
        if last_build:
            if last_build.success:
                file_path = badge_path % 'passing'
            else:
                file_path = badge_path % 'failing'

    try:
        with open(file_path) as fd:
            return HttpResponse(
                fd.read(),
                content_type='image/svg+xml',
            )
    except (IOError, OSError):
        log.exception(
            'Failed to read local filesystem while serving a docs badge',
        )
        return HttpResponse(status=503)


def project_downloads(request, project_slug):
    """A detail view for a project with various downloads."""
    project = get_object_or_404(
        Project.objects.protected(request.user),
        slug=project_slug,
    )
    versions = Version.internal.public(user=request.user, project=project)
    versions = sort_version_aware(versions)
    version_data = OrderedDict()
    for version in versions:
        data = version.get_downloads()
        # Don't show ones that have no downloads.
        if data:
            version_data[version] = data

    return render(
        request,
        'projects/project_downloads.html',
        {
            'project': project,
            'version_data': version_data,
            'versions': versions,
        },
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

    # Send media download to analytics - sensitive data is anonymized
    analytics_event.delay(
        event_category='Build Media',
        event_action=f'Download {type_}',
        event_label=str(version),
        ua=request.META.get('HTTP_USER_AGENT'),
        uip=get_client_ip(request),
    )

    if settings.DEFAULT_PRIVACY_LEVEL == 'public' or settings.DEBUG:

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        storage_path = version.project.get_storage_path(
            type_=type_, version_slug=version_slug,
            version_type=version.type,
        )
        if storage.exists(storage_path):
            return HttpResponseRedirect(storage.url(storage_path))

        media_path = os.path.join(
            settings.MEDIA_URL,
            type_,
            project_slug,
            version_slug,
            '%s.%s' % (project_slug, type_.replace('htmlzip', 'zip')),
        )
        return HttpResponseRedirect(media_path)

    # Get relative media path
    path = (
        version.project.get_production_media_path(
            type_=type_,
            version_slug=version_slug,
        ).replace(settings.PRODUCTION_ROOT, '/prod_artifacts')
    )
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(content_type=content_type)
    if encoding:
        response['Content-Encoding'] = encoding
    response['X-Accel-Redirect'] = path
    # Include version in filename; this fixes a long-standing bug
    filename = '{}-{}.{}'.format(
        project_slug,
        version_slug,
        path.split('.')[-1],
    )
    response['Content-Disposition'] = 'filename=%s' % filename
    return response


def project_versions(request, project_slug):
    """
    Project version list view.

    Shows the available versions and lets the user choose which ones to build.
    """
    project = get_object_or_404(
        Project.objects.protected(request.user),
        slug=project_slug,
    )

    versions = Version.internal.public(
        user=request.user,
        project=project,
        only_active=False,
    )
    active_versions = versions.filter(active=True)
    inactive_versions = versions.filter(active=False)

    # If there's a wiped query string, check the string against the versions
    # list and display a success message. Deleting directories doesn't know how
    # to fail.  :)
    wiped = request.GET.get('wipe', '')
    wiped_version = versions.filter(slug=wiped)
    if wiped and wiped_version.count():
        messages.success(request, 'Version wiped: ' + wiped)

    # Optimize project permission checks
    prefetch_related_objects([project], 'users')

    return render(
        request,
        'projects/project_version_list.html',
        {
            'inactive_versions': inactive_versions,
            'active_versions': active_versions,
            'project': project,
        },
    )


def project_analytics(request, project_slug):
    """Have a analytics API placeholder."""
    project = get_object_or_404(
        Project.objects.protected(request.user),
        slug=project_slug,
    )
    analytics_cache = cache.get('analytics:%s' % project_slug)
    if analytics_cache:
        analytics = json.loads(analytics_cache)
    else:
        try:
            resp = requests.get(
                '{host}/api/v1/index/1/heatmap/'.format(
                    host=settings.GROK_API_HOST,
                ),
                params={'project': project.slug, 'days': 7, 'compare': True},
            )
            analytics = resp.json()
            cache.set('analytics:%s' % project_slug, resp.content, 1800)
        except requests.exceptions.RequestException:
            analytics = None

    if analytics:
        page_list = list(
            reversed(
                sorted(
                    list(analytics['page'].items()),
                    key=operator.itemgetter(1),
                ),
            ),
        )
        version_list = list(
            reversed(
                sorted(
                    list(analytics['version'].items()),
                    key=operator.itemgetter(1),
                ),
            ),
        )
    else:
        page_list = []
        version_list = []

    full = request.GET.get('full')
    if not full:
        page_list = page_list[:20]
        version_list = version_list[:20]

    return render(
        request,
        'projects/project_analytics.html',
        {
            'project': project,
            'analytics': analytics,
            'page_list': page_list,
            'version_list': version_list,
            'full': full,
        },
    )


def project_embed(request, project_slug):
    """Have a content API placeholder."""
    project = get_object_or_404(
        Project.objects.protected(request.user),
        slug=project_slug,
    )
    version = project.versions.get(slug=LATEST)
    files = version.imported_files.filter(
        name__endswith='.html',
    ).order_by('path')

    return render(
        request,
        'projects/project_embed.html',
        {
            'project': project,
            'files': files,
            'settings': {
                'PUBLIC_API_URL': settings.PUBLIC_API_URL,
                'URI': request.build_absolute_uri(location='/').rstrip('/'),
            },
        },
    )
