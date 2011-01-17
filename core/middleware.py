import re

from django.core.cache import cache
from django.core.urlresolvers import get_urlconf, get_resolver, Resolver404
from django.http import Http404


from projects.views.public import slug_detail, subdomain_handler

class SubdomainMiddleware(object):
    def process_request(self, request):
        host = request.get_host()
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')
        if (len(domain_parts) > 2):
            subdomain = domain_parts[0]
            request.slug = subdomain
            if not (subdomain.lower() == 'www') and 'readthedocs' in host:
                request.subdomain = True
                return subdomain_handler(request, subdomain, request.path.lstrip('/'))
        if 'readthedocs' not in host \
            and 'localhost' not in host \
            and 'testserver' not in host:
            request.cname = True
            try:
                slug = cache.get(host)
                if not slug:
                    from dns import resolver
                    answer = [ans for ans in resolver.query(host, 'CNAME')][0]
                    domain = answer.target.to_unicode()
                    slug = domain.split('.')[0]
                    cache.set(host, slug, 60*60)
                request.slug = slug
                return subdomain_handler(request,
                                         slug,
                                         request.path.lstrip('/'))
            except:
                #Some crazy person is CNAMEing to us. 404.
                raise Http404('Invalid Host Name.')
        #Normal request.
        return None
