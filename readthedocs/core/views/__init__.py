"""
Core views.

Including the main homepage, documentation and header rendering,
and server errors.
"""

import logging

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView

from readthedocs.builds.models import Version
from readthedocs.core.utils.general import wipe_version_via_slugs
from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


class NoProjectException(Exception):
    pass


class HomepageView(TemplateView):

    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        """Add latest builds and featured projects."""
        context = super().get_context_data(**kwargs)
        context['featured_list'] = Project.objects.filter(featured=True)
        return context


class SupportView(TemplateView):
    template_name = 'support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        support_email = settings.SUPPORT_EMAIL
        if not support_email:
            support_email = 'support@{domain}'.format(
                domain=settings.PRODUCTION_DOMAIN
            )

        context['support_email'] = support_email
        return context


def wipe_version(request, project_slug, version_slug):
    version = get_object_or_404(
        Version.internal.all(),
        project__slug=project_slug,
        slug=version_slug,
    )
    # We need to check by ``for_admin_user`` here to allow members of the
    # ``Admin`` team (which doesn't own the project) under the corporate site.
    if version.project not in Project.objects.for_admin_user(user=request.user):
        raise Http404('You must own this project to wipe it.')

    if request.method == 'POST':
        wipe_version_via_slugs(
            version_slug=version_slug,
            project_slug=project_slug,
        )
        return redirect('project_version_list', project_slug)
    return render(
        request,
        'wipe_version.html',
        {'version': version, 'project': version.project},
    )


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
