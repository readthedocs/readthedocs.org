from django.conf.urls.defaults import url, patterns, include

from urls import urlpatterns as main_patterns

urlpatterns = patterns('',
    url(r'^(?P<lang_slug>\w{2})/(?P<version_slug>[\w.-]+)/(?P<filename>.+)$',
        'core.views.serve_docs',
        name='docs_detail'
    ),
    url(r'^(?P<lang_slug>\w{2})/(?P<version_slug>.*)/$',
        'core.views.serve_docs',
        {'filename': 'index.html'},
        name='docs_detail'
    ),
    url(r'^(?P<version_slug>.*)/$',
        'projects.views.public.subdomain_handler',
        name='version_subdomain_handler'
    ),
    url(r'^$', 'projects.views.public.subdomain_handler'),
)

urlpatterns += main_patterns
