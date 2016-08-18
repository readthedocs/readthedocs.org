from urlparse import urlparse

from corsheaders import signals

from readthedocs.projects.models import Project, Domain


WHITELIST_URLS = ['/api/v2/footer_html', '/api/v2/search']


def handler(sender, request, **kwargs):
    host = urlparse(request.META['HTTP_ORIGIN']).netloc.split(':')[0]
    valid_url = False
    for url in WHITELIST_URLS:
        if request.path_info.startswith(url):
            valid_url = True

    if valid_url:
        project_slug = request.GET.get('project', None)
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return False

        domain = Domain.objects.filter(
            domain__icontains=host,
            project=project
        )
        if domain.exists():
            return True

    return False

signals.check_request_enabled.connect(handler)
