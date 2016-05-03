from operator import add

from django.conf.urls import url, patterns
from django.conf import settings
from django.conf.urls.static import static

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'

single_version_urls = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    # Handle /docs on RTD domain
    url(r'^docs/(?P<project_slug>[-\w]+)/(?P<filename>.*)$',
        'readthedocs.core.views.serve.serve_docs',
        name='docs_detail'),

    # Handle subdomains
    url(r'^(?P<filename>.*)$',
        'readthedocs.core.views.serve.serve_docs',
        name='docs_detail'),
)

groups = [single_version_urls]

# Needed to serve media locally
if getattr(settings, 'DEBUG', False):
    groups.insert(0, static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns = reduce(add, groups)
