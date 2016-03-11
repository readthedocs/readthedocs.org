import logging

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404

from readthedocs.projects.models import Project, Domain

log = logging.getLogger(__name__)

LOG_TEMPLATE = u"(Middleware) {msg} [{host}{path}]"


class SubdomainMiddleware(object):

    def process_request(self, request):
        if getattr(settings, 'USE_SUBDOMAIN', False):
            return None

        host = request.get_host().lower()
        path = request.get_full_path()
        log_kwargs = dict(host=host, path=path)
        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        if public_domain is None:
            public_domain = settings.PRODUCTION_DOMAIN
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')

        # Serve subdomains - but don't depend on the production domain only having 2 parts
        if len(domain_parts) == len(public_domain.split('.')) + 1:
            subdomain = domain_parts[0]
            is_www = subdomain.lower() == 'www'
            is_ssl = subdomain.lower() == 'ssl'
            if not is_www and not is_ssl and public_domain in host:
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = 'readthedocs.core.subdomain_urls'
                return None
        # Serve CNAMEs
        if (public_domain not in host and
                'localhost' not in host and
                'testserver' not in host):
            request.cname = True
            domains = Domain.objects.filter(domain=host)
            if domains.count():
                for domain in domains:
                    if domain.domain == host:
                        request.slug = domain.project.slug
                        request.urlconf = 'core.subdomain_urls'
                        request.domain_object = True
                        log.debug(LOG_TEMPLATE.format(
                            msg='Domain Object Detected: %s' % domain.domain,
                            **log_kwargs))
                        break
            if (not hasattr(request, 'domain_object') and
                    'HTTP_X_RTD_SLUG' in request.META):
                request.slug = request.META['HTTP_X_RTD_SLUG'].lower()
                request.urlconf = 'readthedocs.core.subdomain_urls'
                request.rtdheader = True
                log.debug(LOG_TEMPLATE.format(
                    msg='X-RTD-Slug header detetected: %s' % request.slug,
                    **log_kwargs))
            # Try header first, then DNS
            elif not hasattr(request, 'domain_object'):
                try:
                    slug = cache.get(host)
                    if not slug:
                        from dns import resolver
                        answer = [ans for ans in resolver.query(host, 'CNAME')][0]
                        domain = answer.target.to_unicode().lower()
                        slug = domain.split('.')[0]
                        cache.set(host, slug, 60 * 60)
                        # Cache the slug -> host mapping permanently.
                        log.debug(LOG_TEMPLATE.format(
                            msg='CNAME cached: %s->%s' % (slug, host),
                            **log_kwargs))
                    request.slug = slug
                    request.urlconf = 'readthedocs.core.subdomain_urls'
                    log.debug(LOG_TEMPLATE.format(
                        msg='CNAME detetected: %s' % request.slug,
                        **log_kwargs))
                except:
                    # Some crazy person is CNAMEing to us. 404.
                    log.exception(LOG_TEMPLATE.format(msg='CNAME 404', **log_kwargs))
                    raise Http404(_('Invalid hostname'))
        # Google was finding crazy www.blah.readthedocs.org domains.
        # Block these explicitly after trying CNAME logic.
        if len(domain_parts) > 3:
            # Stop www.fooo.readthedocs.org
            if domain_parts[0] == 'www':
                log.debug(LOG_TEMPLATE.format(msg='404ing long domain', **log_kwargs))
                raise Http404(_('Invalid hostname'))
            log.debug(LOG_TEMPLATE.format(msg='Allowing long domain name', **log_kwargs))
            # raise Http404(_('Invalid hostname'))
        # Normal request.
        return None


class SingleVersionMiddleware(object):

    """Reset urlconf for requests for 'single_version' docs.

    In settings.MIDDLEWARE_CLASSES, SingleVersionMiddleware must follow
    after SubdomainMiddleware.

    """

    def _get_slug(self, request):
        """Get slug from URLs requesting docs.

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

            if (getattr(proj, 'single_version', False) and
                    not getattr(settings, 'USE_SUBDOMAIN', False)):
                request.urlconf = 'readthedocs.core.single_version_urls'
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
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    Note that this does NOT validate HTTP_X_FORWARDED_FOR. If you're not behind
    a reverse proxy that sets HTTP_X_FORWARDED_FOR automatically, do not use
    this middleware. Anybody can spoof the value of HTTP_X_FORWARDED_FOR, and
    because this sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, that means
    anybody can "fake" their IP address. Only use this when you can absolutely
    trust the value of HTTP_X_FORWARDED_FOR.
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

    def process_request(self, request):
        if ('api/v2/footer_html' in request.path_info and
                settings.SESSION_COOKIE_NAME not in request.COOKIES):
            # Hack request.session otherwise the Authentication middleware complains.
            request.session = {}
            return
        super(FooterNoSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        if ('api/v2/footer_html' in request.path_info and
                settings.SESSION_COOKIE_NAME not in request.COOKIES):
            return response
        return super(FooterNoSessionMiddleware, self).process_response(request, response)
