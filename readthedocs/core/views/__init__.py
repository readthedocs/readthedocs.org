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

from readthedocs.core.mixins import CDNCacheControlMixin, PrivateViewMixin
from readthedocs.projects.models import Project
from readthedocs.proxito.exceptions import (
    ProxitoHttp404,
    ProxitoProjectHttp404,
    ProxitoProjectPageHttp404,
    ProxitoProjectTranslationHttp404,
    ProxitoProjectVersionHttp404,
    ProxitoSubProjectHttp404,
)

log = structlog.get_logger(__name__)


class NoProjectException(Exception):
    pass


class HealthCheckView(CDNCacheControlMixin, View):
    # Never cache this view, we always want to get the live response from the server.
    # In production we should configure the health check to hit the LB directly,
    # but it's useful to be careful here in case of a misconfiguration.
    cache_response = False

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
    """
    Serves a 404 error message, handling 404 exception types raised throughout the app.

    Notice that handling of 404 errors happens elsewhere in views and middleware,
    this view is expected to serve an actual 404 message.
    """

    context = {}
    # Properties are set by ProxitoHttp404. We could also have a look at the
    # subproject_slug
    if isinstance(exception, ProxitoHttp404):
        # These attributes are not guaranteed.
        context.update(
            {
                "project": getattr(exception, "project", None),
                "project_slug": getattr(exception, "project_slug", None),
                "subproject_slug": getattr(exception, "subproject_slug", None),
                "version_slug": getattr(exception, "version_slug", None),
                "language_slug": getattr(exception, "language_slug", None),
                "path_not_found": getattr(exception, "proxito_path", None),
            }
        )

    context["path_not_found"] = context.get("path_not_found") or request.path

    if isinstance(exception, ProxitoProjectVersionHttp404):
        template_name = "errors/404/no_version.html"
    elif isinstance(exception, ProxitoSubProjectHttp404):
        template_name = "errors/404/no_subproject.html"
    elif isinstance(exception, ProxitoProjectTranslationHttp404):
        template_name = "errors/404/no_language.html"
    elif isinstance(exception, ProxitoProjectPageHttp404):
        template_name = "errors/404/no_project_page.html"
    elif isinstance(exception, ProxitoProjectHttp404):
        template_name = "errors/404/no_project.html"

    r = render(
        request,
        template_name,
        context=context,
    )
    r.status_code = 404
    return r


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
