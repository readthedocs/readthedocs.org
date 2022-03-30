"""
Core views.

Including the main homepage, documentation and header rendering,
and server errors.
"""

import structlog

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View, TemplateView

from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.projects.models import Project

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


def server_error_500(request, template_name='500.html'):
    """A simple 500 handler so we get media."""
    r = render(request, template_name)
    r.status_code = 500
    return r


def do_not_track(request):
    dnt_header = request.META.get('HTTP_DNT')

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
