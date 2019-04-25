# -*- coding: utf-8 -*-

"""URL configuration for a single version."""
from functools import reduce
from operator import add

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from readthedocs.constants import pattern_opts
from readthedocs.core.views import serve


handler500 = 'readthedocs.core.views.server_error_500'
handler404 = 'readthedocs.core.views.server_error_404'

single_version_urls = [
    url(
        r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
        r'page/(?P<filename>.*)$'.format(**pattern_opts),
        serve.redirect_page_with_filename,
        name='docs_detail',
    ),
    url(
        (
            r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
            r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
        ),
        serve.serve_docs,
        name='docs_detail',
    ),
]

groups = [single_version_urls]

# Needed to serve media locally
if settings.DEBUG:
    groups.insert(
        0,
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    )

# Allow `/docs/<foo>` URL's when not using subdomains or during local dev
if not settings.USE_SUBDOMAIN or settings.DEBUG:
    docs_url = [
        url(
            (
                r'^docs/(?P<project_slug>[-\w]+)/'
                r'(?:|projects/(?P<subproject_slug>{project_slug})/)'
                r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
            ),
            serve.serve_docs,
            name='docs_detail',
        ),
    ]
    groups.insert(1, docs_url)

urlpatterns = reduce(add, groups)
