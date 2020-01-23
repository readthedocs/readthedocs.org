"""Public project views."""

import hashlib
import json
import logging
import mimetypes
import operator
import os
from urllib.parse import urlparse
from collections import OrderedDict

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.files.storage import get_storage_class
from django.db.models import prefetch_related_objects
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView, ListView
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes
from taggit.models import Tag

from readthedocs.analytics.tasks import analytics_event
from readthedocs.analytics.utils import get_client_ip
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.builds.views import BuildTriggerMixin
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Project
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.proxito.views.mixins import ServeDocsMixin
from readthedocs.proxito.views.utils import _get_project_data_from_request

from .base import ProjectOnboardMixin
from ..constants import PRIVATE


log = logging.getLogger(__name__)
search_log = logging.getLogger(__name__ + '.search')
mimetypes.add_type('application/epub+zip', '.epub')


class ProjectTagIndex(ListView):

    """List view of public :py:class:`Project` instances."""

    model = Project

    def get_queryset(self):
        queryset = Project.objects.public(self.request.user)
        queryset = queryset.exclude(users__profile__banned=True)

        self.tag = get_object_or_404(Tag, slug=self.kwargs.get('tag'))
        queryset = queryset.filter(tags__slug__in=[self.tag.slug])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

        context['badge_url'] = ProjectBadgeView.get_badge_url(
            project.slug,
            version_slug,
            protocol=protocol,
        )
        context['site_url'] = '{url}?badge={version}'.format(
            url=project.get_docs_url(version_slug),
            version=version_slug,
        )

        return context


class ProjectBadgeView(View):

    """
    Return a sweet badge for the project.

    Query parameters:

    * ``version`` the version for the project (latest [default], stable, etc.)
    * ``style`` the style of the badge (flat [default], plastic, etc.)
    * ``token`` a project-specific token needed to access private versions
    """

    http_method_names = ['get', 'head', 'options']
    STATUS_UNKNOWN = 'unknown'
    STATUS_PASSING = 'passing'
    STATUS_FAILING = 'failing'
    STATUSES = (STATUS_FAILING, STATUS_PASSING, STATUS_UNKNOWN)

    def get(self, request, project_slug, *args, **kwargs):
        status = self.STATUS_UNKNOWN
        token = request.GET.get('token')
        version_slug = request.GET.get('version', LATEST)
        version = None

        if token:
            version_to_check = Version.objects.filter(
                project__slug=project_slug,
                slug=version_slug,
            ).first()
            if version_to_check and self.verify_project_token(token, project_slug):
                version = version_to_check
        else:
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
                    status = self.STATUS_PASSING
                else:
                    status = self.STATUS_FAILING

        return self.serve_badge(request, status)

    def get_style(self, request):
        style = request.GET.get('style', 'flat')
        if style not in (
            'flat',
            'plastic',
            'flat-square',
            'for-the-badge',
            'social',
        ):
            style = 'flat'

        return style

    def serve_badge(self, request, status):
        style = self.get_style(request)
        if status not in self.STATUSES:
            status = self.STATUS_UNKNOWN

        badge_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'static',
            'projects',
            'badges',
            f'{status}-{style}.svg',
        )

        try:
            with open(badge_path) as fd:
                return HttpResponse(
                    fd.read(),
                    content_type='image/svg+xml',
                )
        except (IOError, OSError):
            log.exception(
                'Failed to read local filesystem while serving a docs badge',
            )
            return HttpResponse(status=503)

    @classmethod
    def get_badge_url(cls, project_slug, version_slug, protocol='https'):
        url = '{}://{}{}?version={}'.format(
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse('project_badge', args=[project_slug]),
            version_slug,
        )

        # Append a token for private versions
        version = Version.objects.filter(
            project__slug=project_slug,
            slug=version_slug,
        ).first()
        if version and version.privacy_level == PRIVATE:
            token = cls.get_project_token(project_slug)
            url += f'&token={token}'

        return url

    @classmethod
    def get_project_token(cls, project_slug):
        salt = b"readthedocs.projects.views.public.ProjectBadgeView"
        hash_id = hashlib.sha256()
        hash_id.update(force_bytes(settings.SECRET_KEY))
        hash_id.update(salt)
        hash_id.update(force_bytes(project_slug))
        return hash_id.hexdigest()

    @classmethod
    def verify_project_token(cls, token, project_slug):
        expected_token = cls.get_project_token(project_slug)
        return constant_time_compare(token, expected_token)


project_badge = never_cache(ProjectBadgeView.as_view())


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


class ProjectDownloadMediaBase(ServeDocsMixin, View):

    # Use new-style URLs (same domain as docs) or old-style URLs (dashboard URL)
    same_domain_url = False

    def get(
            self,
            request,
            project_slug=None,
            type_=None,
            version_slug=None,
            lang_slug=None,
            subproject_slug=None,
    ):
        """
        Download a specific piece of media.

        Perform an auth check if serving in private mode.

        This view is used to download a file using old-style URLs (download from
        the dashboard) and new-style URLs (download from the same domain as
        docs). Basically, the parameters received by the GET view are different
        (``project_slug`` does not come in the new-style URLs, for example) and
        we need to take it from the request. Once we get the final ``version``
        to be served, everything is the same for both paths.

        .. warning:: This is linked directly from the HTML pages.
                     It should only care about the Version permissions,
                     not the actual Project permissions.
        """
        if self.same_domain_url:
            version = self._version_same_domain_url(
                request,
                type_,
                lang_slug,
                version_slug,
                subproject_slug,
            )
        else:
            version = self._version_dashboard_url(
                request,
                project_slug,
                type_,
                version_slug,
            )

        # Send media download to analytics - sensitive data is anonymized
        analytics_event.delay(
            event_category='Build Media',
            event_action=f'Download {type_}',
            event_label=str(version),
            ua=request.META.get('HTTP_USER_AGENT'),
            uip=get_client_ip(request),
        )

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        storage_path = version.project.get_storage_path(
            type_=type_,
            version_slug=version_slug,
            version_type=version.type,
        )

        # URL without scheme and domain to perform an NGINX internal redirect
        url = storage.url(storage_path)
        url = urlparse(url)._replace(scheme='', netloc='').geturl()

        return self._serve_docs(
            request,
            final_project=version.project,
            version_slug=version.slug,
            path=url,
            download=True,
        )

    def _version_same_domain_url(
            self,
            request,
            type_,
            lang_slug,
            version_slug,
            subproject_slug=None,
    ):
        """
        Return the version to be served (new-style URLs).

        It uses the request to get the ``project``. The rest of arguments come
        from the URL.
        """
        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=None,
            subproject_slug=subproject_slug,
            lang_slug=lang_slug,
            version_slug=version_slug,
        )

        if not self.allowed_user(request, final_project, version_slug):
            return self.get_unauthed_response(request, final_project)

        version = final_project.versions.public(user=request.user).filter(slug=version_slug).first()
        return version

    def _version_dashboard_url(self, request, project_slug, type_, version_slug):
        """
        Return the version to be served (old-style URLs).

        All the arguments come from the URL.
        """
        version = get_object_or_404(
            Version.objects.public(user=request.user),
            project__slug=project_slug,
            slug=version_slug,
        )
        return version


class ProjectDownloadMedia(SettingsOverrideObject):
    _default_class = ProjectDownloadMediaBase


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

    # Limit inactive versions in case a project has a large number of branches or tags
    # Filter inactive versions based on the query string
    inactive_versions = versions.filter(active=False)
    version_filter = request.GET.get('version_filter', '')
    if version_filter:
        inactive_versions = inactive_versions.filter(verbose_name__icontains=version_filter)
    inactive_versions = inactive_versions[:100]

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
