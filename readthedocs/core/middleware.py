from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.cache import cache
from django.http import Http404

import redis


class SubdomainMiddleware(object):
    def process_request(self, request):
        if settings.DEBUG:
            return None
        host = request.get_host()
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')

        # Google was finding crazy www.blah.readthedocs.org domains.
        if len(domain_parts) > 3:
            # Let's try allowing this again.
            pass
            #raise Http404(_('Invalid hostname'))
        if len(domain_parts) == 3:
            subdomain = domain_parts[0]
            # Serve subdomains
            is_www = subdomain.lower() == 'www'
            is_ssl = subdomain.lower() == 'ssl'
            if not is_www and not is_ssl and 'readthedocs.org' in host:
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = 'core.subdomain_urls'
                return None
            # Serve rtfd.org
            elif not is_www and not is_ssl and 'rtfd.org' in host:
                request.slug = subdomain
                request.urlconf = 'core.djangome_urls'
                return None
        # Serve CNAMEs
        if 'readthedocs.org' not in host and \
           'localhost' not in host and \
           'testserver' not in host:
            request.cname = True
            try:
                request.slug = request.META['HTTP_X_RTD_SLUG']
                request.urlconf = 'core.subdomain_urls'
                request.rtdheader = True
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
                except:
                    # Some crazy person is CNAMEing to us. 404.
                    raise Http404(_('Invalid Host Name.'))
        # Normal request.
        return None
