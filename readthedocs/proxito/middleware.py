import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import Http404

from readthedocs.projects.models import Domain

log = logging.getLogger(__name__)


def map_host_to_project(request):
    """
    Take the incoming host, and map it to the proper Project.

    We check, in order:

    * The ``HTTP_X_RTD_SLUG`` host header for explicit Project mapping
    * The ``PUBLIC_DOMAIN`` where we can use the subdomain as the project name
    * The hostname without port information, which maps to ``Domain`` objects
    """

    host = request.get_host().lower().split(':')[0]
    public_domain = settings.PUBLIC_DOMAIN.lower().split(':')[0]
    host_parts = host.split('.')
    public_domain_parts = public_domain.split('.')

    # Explicit Project slug being passed in
    if 'HTTP_X_RTD_SLUG' in request.META:
        project = request.META['HTTP_X_RTD_SLUG'].lower()
        request.rtdheader = True

    elif public_domain in host:
        # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`
        if public_domain_parts == host_parts[1:]:
            project = host_parts[0]
            request.subdomain = True
            log.debug('Proxito Public Domain: %s', host)
        else:
            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example
            # But these feel like they might be phishing, etc. so let's block them for now.
            project = None
            log.warning('Weird variation on our hostname: %s', host)
            raise Http404(f'404: Invalid domain matching {public_domain}')

    # Serve CNAMEs
    else:
        domain_qs = Domain.objects.filter(domain=host).prefetch_related('project')
        if domain_qs.exists():
            project = domain_qs.first().project.slug
            request.cname = True
            log.debug('Proxito CNAME: %s', host)
        else:
            # Some person is CNAMEing to us without configuring a domain - 404.
            project = None
            log.debug('CNAME 404: %s', host)
            raise Http404('CNAME 404')
    log.debug('Proxito Project: %s', project)
    return project


class ProxitoMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        if not settings.USE_SUBDOMAIN:
            raise MiddlewareNotUsed('USE_SUBDOMAIN setting is not on')

    def __call__(self, request):
        # For local dev to hit the main site
        if 'localhost' in request.get_host() or 'testserver' in request.get_host():
            return self.get_response(request)

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        host_project = map_host_to_project(request)
        request.host_project_slug = host_project
        request.slug = host_project
        request.urlconf = 'readthedocs.proxito.urls'

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
