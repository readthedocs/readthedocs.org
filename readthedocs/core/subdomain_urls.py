from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('',
    url(r'^(?P<lang_slug>\w{2})/(?P<version_slug>[\w.-]+)/(?P<filename>.+)$',
        'projects.views.public.subdomain_handler',
        name='version_subdomain_handler'
    ),
    url(r'^en/(?P<version_slug>.*)/$',
        'projects.views.public.subdomain_handler',
        name='version_subdomain_handler'
    ),
    url(r'^(?P<version_slug>.*)/$',
        'projects.views.public.subdomain_handler',
        name='version_subdomain_handler'
    ),
    url(r'^$', 'projects.views.public.subdomain_handler')
)
