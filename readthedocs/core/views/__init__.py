"""
Core views.

Including the main homepage, documentation and header rendering,
and server errors.
"""

import structlog
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, View

from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.projects.models import Project
from readthedocs.proxito.exceptions import (
    ProxitoProjectHttp404,
    ProxitoProjectPageHttp404,
    ProxitoProjectVersionHttp404,
    ProxitoSubProjectHttp404,
)

log = structlog.get_logger(__name__)


class NoProjectException(Exception):
    pass


class HealthCheckView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status': 200}, status=200)


class HomepageView(TemplateView):

    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        """Add latest builds and featured projects."""
        context = super().get_context_data(**kwargs)
        context['featured_list'] = Project.objects.filter(featured=True)
        return context


class SupportView(PrivateViewMixin, TemplateView):

    template_name = 'support/index.html'

    def get_context_data(self, **kwargs):
        """Pass along endpoint for support form."""
        context = super().get_context_data(**kwargs)
        context['SUPPORT_FORM_ENDPOINT'] = settings.SUPPORT_FORM_ENDPOINT
        return context


def server_error_404(request, template_name="errors/404/base.html", exception=None):
    """Generic 404 handler, handling 404 exception types raised throughout the app"""

    try:
        log.debug("404 view handler active")
        log.debug(exception)
        # Properties are set by ProxitoHttp404. We could also have a look at the
        # subproject_slug
        project_slug = getattr(exception, "project_slug", None)
        version_slug = getattr(exception, "version_slug", None)
        project = getattr(exception, "project", None)
        subproject_slug = getattr(exception, "subproject_slug", None)

        if isinstance(exception, ProxitoProjectVersionHttp404):
            template_name = "errors/404/no_version.html"
        elif isinstance(exception, ProxitoSubProjectHttp404):
            template_name = "errors/404/no_subproject.html"
        elif isinstance(exception, ProxitoProjectPageHttp404):
            template_name = "errors/404/no_project_page.html"
        elif isinstance(exception, ProxitoProjectHttp404):
            template_name = "errors/404/no_project.html"

        r = render(
            request,
            template_name,
            context={
                "project": project,
                "project_slug": project_slug,
                "subproject_slug": subproject_slug,
                "version_slug": version_slug,
            },
        )
        r.status_code = 404
        return r
    except Exception as e:
        log.debug(e)


def server_error_500(request, template_name='500.html'):
    """A simple 500 handler so we get media."""
    r = render(request, template_name)
    r.status_code = 500
    return r


def do_not_track(request):
    dnt_header = request.headers.get("Dnt")

    # https://w3c.github.io/dnt/drafts/tracking-dnt.html#status-representation
    return JsonResponse(  # pylint: disable=redundant-content-type-for-json-response
        {
            'policy': 'https://docs.readthedocs.io/en/latest/privacy-policy.html',
            'same-party': [
                'readthedocs.org',
                'readthedocs.com',
                'readthedocs.io',           # .org Documentation Sites
                'readthedocs-hosted.com',   # .com Documentation Sites
            ],
            'tracking': 'N' if dnt_header == '1' else 'T',
        }, content_type='application/tracking-status+json',
    )
