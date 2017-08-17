"""URL configurations for subdomains."""
from __future__ import absolute_import

from functools import reduce
from operator import add

from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

from readthedocs.core.views.serve import (
    redirect_page_with_filename,
    redirect_project_slug, serve_docs
)
from readthedocs.core.views import (
    server_error_500,
    server_error_404,
)
from readthedocs.constants import pattern_opts

handler500 = server_error_500
handler404 = server_error_404

subdomain_urls = [
    url(r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
        r'page/(?P<filename>.*)$'.format(**pattern_opts),
        redirect_page_with_filename,
        name='docs_detail'),

    url((r'^(?:|projects/(?P<subproject_slug>{project_slug})/)$').format(**pattern_opts),
        redirect_project_slug,
        name='redirect_project_slug'),

    url((r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
         r'(?P<lang_slug>{lang_slug})/'
         r'(?P<version_slug>{version_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        serve_docs,
        name='docs_detail'),
]

groups = [subdomain_urls]

# Needed to serve media locally
if getattr(settings, 'DEBUG', False):
    groups.insert(0, static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

urlpatterns = reduce(add, groups)
