from operator import add

from django.conf.urls import url, patterns
from django.conf import settings
from django.conf.urls.static import static

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'

subdomain_urls = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url(r'^page/(?P<filename>.*)$',
        'readthedocs.core.views.serve.redirect_page_with_filename',
        name='docs_detail'),

    url(r'^$', 'readthedocs.core.views.serve.redirect_project_slug', name='redirect_project_slug'),
    url(r'^(?P<filename>.*)$',
        'readthedocs.core.views.serve.serve_symlink_docs',
        name='docs_detail'),
)

groups = [subdomain_urls]

if getattr(settings, 'DEBUG', False):
    groups.insert(0, static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns = reduce(add, groups)
