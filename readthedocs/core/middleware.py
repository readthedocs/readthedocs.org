import logging

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.cache import cache
from django.http import Http404

import redis

log = logging.getLogger(__name__)

LOG_TEMPLATE = "(Middleware) {msg} [{host}{path}]"

class SubdomainMiddleware(object):
    def process_request(self, request):
        host = request.get_host()
        path = request.get_full_path()
        log_kwargs = dict(host=host, path=path)
        if settings.DEBUG:
            log.debug(LOG_TEMPLATE.format(msg='DEBUG on, not processing middleware', **log_kwargs))
            return None
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')

        if len(domain_parts) == 3:
            subdomain = domain_parts[0]
            # Serve subdomains
            is_www = subdomain.lower() == 'www'
            is_ssl = subdomain.lower() == 'ssl'
            if not is_www and not is_ssl and settings.PRODUCTION_DOMAIN in host:
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = 'core.subdomain_urls'
                return None
            # Serve rtfd.org
            elif not is_www and not is_ssl and 'rtfd.org' in host:
                # Disable RTFD django.me close stuff for now.
                # AFAICT nobody uses it, and it causes 500s in templates :)
                continue
                request.slug = subdomain
                request.urlconf = 'core.djangome_urls'
                log.debug(LOG_TEMPLATE.format(msg='Django.me request let through', **log_kwargs))
                return None
        # Serve CNAMEs
        if settings.PRODUCTION_DOMAIN not in host and \
           'localhost' not in host and \
           'testserver' not in host:
            request.cname = True
            try:
                request.slug = request.META['HTTP_X_RTD_SLUG']
                request.urlconf = 'core.subdomain_urls'
                request.rtdheader = True
                log.debug(LOG_TEMPLATE.format(msg='X-RTD-Slug header detetected: %s' % request.slug, **log_kwargs))
            except KeyError:
                # Try header first, then DNS
                try:
                    slug = cache.get(host)
                    if not slug:
                        redis_conn = redis.Redis(**settings.REDIS)
                        from dns import resolver
                        answer = [ans for ans in resolver.query(host, 'CNAME')][0]
                        domain = answer.target.to_unicode()
                        slug = domain.split('.')[0]
                        cache.set(host, slug, 60*60)
                        #Cache the slug -> host mapping permanently.
                        redis_conn.sadd("rtd_slug:v1:%s" % slug, host)
                    request.slug = slug
                    request.urlconf = 'core.subdomain_urls'
                    log.debug(LOG_TEMPLATE.format(msg='CNAME detetected: %s' % request.slug, **log_kwargs))
                except:
                    # Some crazy person is CNAMEing to us. 404.
                    log.debug(LOG_TEMPLATE.format(msg='CNAME 404', **log_kwargs))
                    raise Http404(_('Invalid Host Name.'))
        # Google was finding crazy www.blah.readthedocs.org domains.
        # Block these explicitly after trying CNAME logic.
        if len(domain_parts) > 3:
            log.debug(LOG_TEMPLATE.format(msg='Blocking long domain name', **log_kwargs))
            raise Http404(_('Invalid hostname'))
        # Normal request.
        return None
