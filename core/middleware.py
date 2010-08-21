import re
from dns import resolver

from django.core.cache import cache
from django.core.urlresolvers import get_urlconf, get_resolver, Resolver404

from projects.views.public import slug_detail

#http://joshuajonah.ca/blog/2010/06/18/poor-mans-esi-nginx-ssis-and-django/
class NginxSSIMiddleware(object):
    '''
    Emulates Nginx SSI module for when a page is rendered from Python. SSI include tags are
    cached for serving directly from Nginx, but if the page is being built for the first time,
    we just serve these directly from Python without having to make another request.

    Takes a response object and returns the response with Nginx SSI tags resolved.
    '''
    def process_response(self, request, response):
        include_tag = r'<!--#[\s.]+include[\s.]+virtual=["\'](?P<path>.+)["\'][\s.]+-->'
        res = get_resolver(get_urlconf())
        patterns = res._get_url_patterns()
        def get_tag_response(match):
            for pattern in patterns:
                try:
                    view = pattern.resolve(match.group('path')[1:])
                    if view:
                        return view[0](request, *view[1], **view[2]).content
                except Resolver404:
                    pass
            return match.group('path')[1:]
        response.content = re.sub(include_tag, get_tag_response, response.content)
        response['Content-Length'] = len(response.content)
        return response

class SubdomainMiddleware(object):
    def process_request(self, request):
        host = request.get_host()
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')
        if (len(domain_parts) > 2):
            subdomain = domain_parts[0]
            if not (subdomain.lower() == 'www') and 'readthedocs' in host:
                return slug_detail(request, subdomain, request.path.lstrip('/'))
        if 'readthedocs' not in host:
            try:
                slug = cache.get(host)
                if not slug:
                    from dns import resolver
                    answer = [ans for ans in resolver.query(host, 'CNAME')][0]
                    domain = answer.target.to_unicode()
                    slug = domain.split('.')[0]
                    cache.set(host, slug, 60*60)
                return slug_detail(request, slug, request.path.lstrip('/'))
            except:
                #Except any error here, because we never want to blow up in this step.
                return None
        return None
