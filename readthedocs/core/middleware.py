"""Middleware for core app."""

from __future__ import absolute_import
from builtins import object
import logging

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import set_urlconf, get_urlconf
from django.http import Http404, HttpResponseBadRequest

from readthedocs.core.utils import cname_to_slug
from readthedocs.projects.models import Project, Domain

log = logging.getLogger(__name__)

LOG_TEMPLATE = u"(Middleware) {msg} [{host}{path}]"
SUBDOMAIN_URLCONF = getattr(
    settings,
    'SUBDOMAIN_URLCONF',
    'readthedocs.core.urls.subdomain'
)
SINGLE_VERSION_URLCONF = getattr(
    settings,
    'SINGLE_VERSION_URLCONF',
    'readthedocs.core.urls.single_version'
)


class SubdomainMiddleware(object):

    """Middleware to display docs for non-dashboard domains."""

    def process_request(self, request):
        """
        Process requests for unhandled domains.

        If the request is not for our ``PUBLIC_DOMAIN``, or if ``PUBLIC_DOMAIN``
        is not set and the request is for a subdomain on ``PRODUCTION_DOMAIN``,
        process the request as a request a documentation project.
        """
        if not getattr(settings, 'USE_SUBDOMAIN', False):
            return None

        full_host = host = request.get_host().lower()
        path = request.get_full_path()
        log_kwargs = dict(host=host, path=path)
        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        production_domain = getattr(
            settings,
            'PRODUCTION_DOMAIN',
            'readthedocs.org'
        )

        if public_domain is None:
            public_domain = production_domain
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')

        # Serve subdomains - but don't depend on the production domain only having 2 parts
        if len(domain_parts) == len(public_domain.split('.')) + 1:
            subdomain = domain_parts[0]
            is_www = subdomain.lower() == 'www'
            if not is_www and (
                # Support ports during local dev
                public_domain in host or public_domain in full_host
            ):
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = SUBDOMAIN_URLCONF
                return None

        # Serve CNAMEs
        if (public_domain not in host and
                production_domain not in host and
                'localhost' not in host and
                'testserver' not in host):
            request.cname = True
            domains = Domain.objects.filter(domain=host)
            if domains.count():
                for domain in domains:
                    if domain.domain == host:
                        request.slug = domain.project.slug
                        request.urlconf = SUBDOMAIN_URLCONF
                        request.domain_object = True
                        log.debug(LOG_TEMPLATE.format(
                            msg='Domain Object Detected: %s' % domain.domain,
                            **log_kwargs))
                        break
            if (not hasattr(request, 'domain_object') and
                    'HTTP_X_RTD_SLUG' in request.META):
                request.slug = request.META['HTTP_X_RTD_SLUG'].lower()
                request.urlconf = SUBDOMAIN_URLCONF
                request.rtdheader = True
                log.debug(LOG_TEMPLATE.format(
                    msg='X-RTD-Slug header detected: %s' % request.slug,
                    **log_kwargs))
            # Try header first, then DNS
            elif not hasattr(request, 'domain_object'):
                try:
                    slug = cache.get(host)
                    if not slug:
                        slug = cname_to_slug(host)
                        cache.set(host, slug, 60 * 60)
                        # Cache the slug -> host mapping permanently.
                        log.info(LOG_TEMPLATE.format(
                            msg='CNAME cached: %s->%s' % (slug, host),
                            **log_kwargs))
                    request.slug = slug
                    request.urlconf = SUBDOMAIN_URLCONF
                    log.warning(LOG_TEMPLATE.format(
                        msg='CNAME detected: %s' % request.slug,
                        **log_kwargs))
                except:  # noqa
                    # Some crazy person is CNAMEing to us. 404.
                    log.warning(LOG_TEMPLATE.format(msg='CNAME 404', **log_kwargs))
                    raise Http404(_('Invalid hostname'))
        # Google was finding crazy www.blah.readthedocs.org domains.
        # Block these explicitly after trying CNAME logic.
        if len(domain_parts) > 3 and not settings.DEBUG:
            # Stop www.fooo.readthedocs.org
            if domain_parts[0] == 'www':
                log.debug(LOG_TEMPLATE.format(msg='404ing long domain', **log_kwargs))
                return HttpResponseBadRequest(_('Invalid hostname'))
            log.debug(LOG_TEMPLATE.format(msg='Allowing long domain name', **log_kwargs))
            # raise Http404(_('Invalid hostname'))
        # Normal request.
        return None

    def process_response(self, request, response):
        # Reset URLconf for this thread
        # to the original one.
        set_urlconf(None)
        return response


class SingleVersionMiddleware(object):

    """
    Reset urlconf for requests for 'single_version' docs.

    In settings.MIDDLEWARE_CLASSES, SingleVersionMiddleware must follow after
    SubdomainMiddleware.
    """

    def _get_slug(self, request):
        """
        Get slug from URLs requesting docs.

        If URL is like '/docs/<project_name>/', we split path
        and pull out slug.

        If URL is subdomain or CNAME, we simply read request.slug, which is
        set by SubdomainMiddleware.
        """
        slug = None
        if hasattr(request, 'slug'):
            # Handle subdomains and CNAMEs.
            slug = request.slug.lower()
        else:
            # Handle '/docs/<project>/' URLs
            path = request.get_full_path()
            path_parts = path.split('/')
            if len(path_parts) > 2 and path_parts[1] == 'docs':
                slug = path_parts[2].lower()
        return slug

    def process_request(self, request):
        slug = self._get_slug(request)
        if slug:
            try:
                proj = Project.objects.get(slug=slug)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # Let 404 be handled further up stack.
                return None

            if getattr(proj, 'single_version', False):
                request.urlconf = SINGLE_VERSION_URLCONF
                # Logging
                host = request.get_host()
                path = request.get_full_path()
                log_kwargs = dict(host=host, path=path)
                log.debug(LOG_TEMPLATE.format(
                    msg='Handling single_version request', **log_kwargs)
                )

        return None


# Forked from old Django
class ProxyMiddleware(object):

    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the.

    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1. Note that this
    does NOT validate HTTP_X_FORWARDED_FOR. If you're not behind a reverse proxy
    that sets HTTP_X_FORWARDED_FOR automatically, do not use this middleware.
    Anybody can spoof the value of HTTP_X_FORWARDED_FOR, and because this sets
    REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, that means anybody can "fake"
    their IP address. Only use this when you can absolutely trust the value of
    HTTP_X_FORWARDED_FOR.
    """

    def process_request(self, request):
        try:
            real_ip = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError:
            return None
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs. The
            # client's IP will be the first one.
            real_ip = real_ip.split(",")[0].strip()
            request.META['REMOTE_ADDR'] = real_ip


class FooterNoSessionMiddleware(SessionMiddleware):

    """
    Middleware that doesn't create a session on logged out doc views.

    This will reduce the size of our session table drastically.
    """

    IGNORE_URLS = ['/api/v2/footer_html', '/sustainability/view', '/sustainability/click']

    def process_request(self, request):
        for url in self.IGNORE_URLS:
            if (request.path_info.startswith(url) and
                    settings.SESSION_COOKIE_NAME not in request.COOKIES):
                # Hack request.session otherwise the Authentication middleware complains.
                request.session = {}
                return
        super(FooterNoSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        for url in self.IGNORE_URLS:
            if (request.path_info.startswith(url) and
                    settings.SESSION_COOKIE_NAME not in request.COOKIES):
                return response
        return super(FooterNoSessionMiddleware, self).process_response(request, response)
