from urlparse import urlparse

from corsheaders import signals

from readthedocs.projects.models import Domain


WHITELIST_URLS = ['/api/v2/footer_html', '/api/v2/search']


def handler(sender, request, **kwargs):
    host = urlparse(request.META['HTTP_ORIGIN']).netloc.split(':')[0]
    domains = Domain.objects.filter(domain__icontains=host)
    if domains.exist():
        for url in WHITELIST_URLS:
            if request.path_info.startswith(url):
                return True
    return False


signals.check_request_enabled.connect(handler)
