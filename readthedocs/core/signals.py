from corsheaders import signals
from readthedocs.projects.models import Domain

from urlparse import urlparse


def handler(sender, request, **kwargs):
    whitelist_urls = ['/api/v2/footer_html', '/api/v2/search']
    host = urlparse(request.META['HTTP_ORIGIN']).netloc.split(':')[0]
    domains = Domain.objects.filter(domain__icontains=host)
    for url in whitelist_urls:
        if (request.path_info.startswith(url) and domains.count()):
            return True
    return False

signals.check_request_enabled.connect(handler)
