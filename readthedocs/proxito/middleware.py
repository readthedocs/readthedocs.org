import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import Http404

from readthedocs.projects.models import Domain

log = logging.getLogger(__name__)


def map_host_to_project(request):
    """
    Take the incoming host, and map it to the proper Project.

    We check:

    * The ``HTTP_X_RTD_SLUG`` host header for explicit Project mapping
    * The ``PUBLIC_DOMAIN`` where we can use the subdomain as the project name
    * The hostname without port information, which maps to ``Domain`` objects
    """

    host_and_port = request.get_host().lower()
    if ':' in host_and_port:
        host = host_and_port.split(':')[0]
    host_parts = host.split('.')

    public_domain = settings.PUBLIC_DOMAIN.split(':')[0]

    # Explicit Project slug being passed in
    if 'HTTP_X_RTD_SLUG' in request.META:
        project = request.META['HTTP_X_RTD_SLUG'].lower()

    # Ensure we don't support `foo.bar.PUBLIC_DOMAIN`
    elif public_domain in host and len(host_parts) == (len(public_domain.split('.')) + 1):
        project = host_parts[0]

    # Serve CNAMEs
    else:
        domain = Domain.objects.get(domain__iexact=host).prefetch_related('project')
        if domain:
            project = domain.project.slug
        else:
            # Some person is CNAMEing to us without configuring a domain - 404.
            project = None
            raise Http404('CNAME 404')
    return project


class ProxitoMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.USE_SUBDOMAIN:
            raise MiddlewareNotUsed('USE_SUBDOMAIN setting is not on')

    def __call__(self, request):
        # For local dev to hit the main site
        if 'localhost' in request.get_host():
            return self.get_response(request)

        # Code to be executed for each request before
        # the view (and later middleware) are called.
        host_project = map_host_to_project(request)
        request.host_project_slug = host_project
        request.urlconf = 'readthedocs.proxito.urls'

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
