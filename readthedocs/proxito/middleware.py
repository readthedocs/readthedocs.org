import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext_lazy as _

from readthedocs.projects.models import Domain


log = logging.getLogger(__name__)


def map_host_to_project_slug(request):
    """
    Take the request and map the host to the proper project slug.

    We check, in order:

    * The ``HTTP_X_RTD_SLUG`` host header for explicit Project mapping
        - This sets ``request.rtdheader`` True
    * The ``PUBLIC_DOMAIN`` where we can use the subdomain as the project name
        - This sets ``request.subdomain`` True
    * The hostname without port information, which maps to ``Domain`` objects
        - This sets ``request.cname`` True
    """

    host = request.get_host().lower().split(':')[0]
    public_domain = settings.PUBLIC_DOMAIN.lower().split(':')[0]
    host_parts = host.split('.')
    public_domain_parts = public_domain.split('.')

    # Explicit Project slug being passed in
    if 'HTTP_X_RTD_SLUG' in request.META:
        project_slug = request.META['HTTP_X_RTD_SLUG'].lower()
        request.rtdheader = True

    elif public_domain in host:
        # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`
        if public_domain_parts == host_parts[1:]:
            project_slug = host_parts[0]
            request.subdomain = True
            log.debug('Proxito Public Domain: %s', host)
        else:
            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example
            # But these feel like they might be phishing, etc. so let's block them for now.
            project_slug = None
            log.warning('Weird variation on our hostname: %s', host)
            return HttpResponseBadRequest(_('Invalid hostname'))

    # Serve CNAMEs
    else:
        domain_qs = Domain.objects.filter(domain=host).prefetch_related('project')
        if domain_qs.exists():
            project_slug = domain_qs.first().project.slug
            request.cname = True
            log.debug('Proxito CNAME: %s', host)
        else:
            # Some person is CNAMEing to us without configuring a domain - 404.
            project_slug = None
            log.debug('CNAME 404: %s', host)
            return render(
                request, 'core/dns-404.html', context={'host': host}, status=404
            )
    log.debug('Proxito Project: %s', project_slug)
    return project_slug


class ProxitoMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if any([not settings.USE_SUBDOMAIN, 'localhost' in request.get_host(),
                'testserver' in request.get_host()]):
            log.debug('Not processing Proxito middleware')
            return None

        ret = map_host_to_project_slug(request)

        # Handle returning a response
        if hasattr(ret, 'status_code'):
            return ret

        # Otherwise set the slug on the request
        request.host_project_slug = request.slug = ret

        return None


class NewStyleProxitoMiddleware:
    # This is the new style middleware, I can't figure out how to test it.

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

        host_project = map_host_to_project_slug(request)
        request.host_project_slug = host_project
        request.slug = host_project
        # request.urlconf = 'readthedocs.proxito.urls'

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
