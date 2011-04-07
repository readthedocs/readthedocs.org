import re

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import get_urlconf, get_resolver, Resolver404
from django.http import Http404
from django.utils.encoding import smart_unicode

import redis


from projects.views.public import slug_detail, subdomain_handler

#Thanks to debug-toolbar for the response-replacing code.
_HTML_TYPES = ('text/html', 'application/xhtml+xml')

OUR_CODE = """
<hr> <!-- End original user content -->
<script type="text/javascript">
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-17997319-1']);
  _gaq.push(['_trackPageview']);
  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
</script>

<style type="text/css">
.badge { position: fixed; display: block; bottom: 5px; height: 40px; text-indent: -9999em; border-radius: 3px; -moz-border-radius: 3px; -webkit-border-radius: 3px; box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset; -moz-box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset; -webkit-box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset; }
.badge.rtd { background: #257597 url(http://media.readthedocs.org/images/badge-rtd.png) top left no-repeat; border: 1px solid #282E32; width: 160px; right: 5px; }
</style>

<a href="http://readthedocs.org?fromdocs=middleware" class="badge rtd">Brought to you by Read the Docs</a>
"""

def replace_insensitive(string, target, replacement):
    """
    Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else: # no results so return the original string
        return string


class SubdomainMiddleware(object):
    def process_request(self, request):
        host = request.get_host()
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')
        #Google was finding crazy www.blah.readthedocs.org domains.
        if len(domain_parts) > 3:
            if not settings.DEBUG:
                raise Http404('Invalid hostname')
        if len(domain_parts) == 3:
            subdomain = domain_parts[0]
            if not (subdomain.lower() == 'www') and 'readthedocs.org' in host:
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = 'core.subdomain_urls'
        if len(domain_parts) == 3:
            subdomain = domain_parts[0]
            if not (subdomain.lower() == 'www') and 'rtfd.org' in host:
                request.slug = subdomain
                request.urlconf = 'core.djangome_urls'
        if 'readthedocs.org' not in host \
            and 'localhost' not in host \
            and 'testserver' not in host:
            request.cname = True
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
                #Some crazy person is CNAMEing to us. 404.
                if not settings.DEBUG:
                    raise Http404('Invalid Host Name.')
        #Normal request.
        return None

    def process_response(self, request, response):
        #Try and make this match as little as possible.
        if response.status_code == 200 and '_static' not in request.path and '_images' not in request.path:
            if getattr(request, 'add_badge', False):
                response.content = replace_insensitive(
                    smart_unicode(response.content),
                    "</body>",
                    smart_unicode(OUR_CODE + "</body>"))
            if response.get('Content-Length', None):
                response['Content-Length'] = len(response.content)
        return response
