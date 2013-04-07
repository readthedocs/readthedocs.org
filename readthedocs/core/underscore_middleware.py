# We aren't serving - domains properly ATM, so turn this off.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, SuspiciousOperation
from django.utils.http import urlquote

import re
from django import http

host_validation_re = re.compile((r"^([a-z0-9_.-]+|\[[a-f0-9]*:[a-f0-9:]+\])'
                                 r'(:\d+)?$"))
#host_validation_re = re.compile((r"^([a-z0-9.-]+|\[[a-f0-9]*:[a-f0-9:]+\])'
                                  r'(:\d+)?$"))
http.host_validation_re = host_validation_re

class UnderscoreMiddleware(object):
    def process_request(self, request):
        # Handle redirect of domains with _ in them.
        host = request.get_host()
        if '_' in host:
            host = host.replace('_', '-')
            new_uri = '%s://%s%s%s' % (
                request.is_secure() and 'https' or 'http',
                host,
                urlquote(request.path),
                (request.method == 'GET'
                 and len(request.GET) > 0)
                 and '?%s' % request.GET.urlencode()
                 or ''
            )
            return HttpResponsePermanentRedirect(new_uri)
"""
