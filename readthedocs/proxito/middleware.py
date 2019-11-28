"""
Middleware for Proxito.

This is used to take the request and map the host to the proper project slug.

Additional processing is done to get the project from the URL in the ``views.py`` as well.
"""
import logging

from django.conf import settings
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from readthedocs.projects.models import Domain

log = logging.getLogger(__name__)  # noqa


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

    project_slug = None

    # Explicit Project slug being passed in
    if 'HTTP_X_RTD_SLUG' in request.META:
        project_slug = request.META['HTTP_X_RTD_SLUG'].lower()
        request.rtdheader = True

    elif public_domain in host or host == 'proxito':
        # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`
        if public_domain_parts == host_parts[1:]:
            project_slug = host_parts[0]
            request.subdomain = True
            log.debug('Proxito Public Domain: host=%s', host)
        else:
            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example
            # But these feel like they might be phishing, etc. so let's block them for now.
            log.warning('Weird variation on our hostname: host=%s', host)
            return render(
                request, 'core/dns-404.html', context={'host': host}, status=400
            )

    # Serve CNAMEs
    else:
        domain = Domain.objects.filter(domain=host).first()
        if domain:
            project_slug = domain.project.slug
            request.cname = True
            log.debug('Proxito CNAME: host=%s', host)
        else:
            # Some person is CNAMEing to us without configuring a domain - 404.
            log.debug('CNAME 404: host=%s', host)
            return render(
                request, 'core/dns-404.html', context={'host': host}, status=404
            )

    log.debug('Proxito Project: slug=%s', project_slug)
    return project_slug


class ProxitoMiddleware(MiddlewareMixin):

    """The actual middleware we'll be using in prod."""

    def process_request(self, request):  # noqa
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
