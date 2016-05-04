from operator import add

from django.conf.urls import url, patterns
from django.conf import settings
from django.conf.urls.static import static

from readthedocs.constants import pattern_opts

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'

single_version_urls = patterns(
    '',  # base view, flake8 complains if it is on the previous line.

    url(r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
        r'page/(?P<filename>.*)$'.format(**pattern_opts),
        'readthedocs.core.views.serve.redirect_page_with_filename',
        name='docs_detail'),

    url((r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.serve.serve_docs',
        name='docs_detail'),
)

groups = [single_version_urls]

# Needed to serve media locally
if getattr(settings, 'DEBUG', False):
    groups.insert(0, static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Allow `/docs/<foo>` URL's when not using subdomains or during local dev
if not getattr(settings, 'USE_SUBDOMAIN', False) or settings.DEBUG:
    docs_url = patterns(
        '',
        url((r'^docs/(?P<project_slug>[-\w]+)/'
             r'(?:|projects/(?P<subproject_slug>{project_slug})/)'
             r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
            'readthedocs.core.views.serve.serve_docs',
            name='docs_detail')
    )
    groups.insert(1, docs_url)


urlpatterns = reduce(add, groups)
