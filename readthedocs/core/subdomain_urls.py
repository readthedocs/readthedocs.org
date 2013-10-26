from django.conf.urls.defaults import url, patterns

from urls import urlpatterns as main_patterns


urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url((r'^projects/(?P<project_slug>[\w.-]+)/(?P<lang_slug>\w{2})/'
         r'(?P<version_slug>[\w.-]+)/(?P<filename>.*)$'),
        'core.views.subproject_serve_docs',
        name='subproject_docs_detail'),

    url(r'^projects/(?P<project_slug>[\w.-]+)',
        'core.views.subproject_serve_docs',
        name='subproject_docs_detail'),

    url(r'^projects/$',
        'core.views.subproject_list',
        name='subproject_docs_list'),

    url(r'^(?P<lang_slug>\w{2})/(?P<version_slug>[\w.-]+)/(?P<filename>.*)$',
        'core.views.serve_docs',
        name='docs_detail'),

    url(r'^(?P<lang_slug>\w{2})/(?P<version_slug>.*)/$',
        'core.views.serve_docs',
        {'filename': 'index.html'},
        name='docs_detail'),

    url(r'^page/(?P<filename>.*)$',
        'core.views.subdomain_handler',
        {
            'version_slug': None,
            'lang_slug': None,
        },
        name='docs_detail'),

    url(r'^(?P<version_slug>.*)/$',
        'core.views.subdomain_handler',
        name='version_subdomain_handler'),

    url(r'^$', 'core.views.subdomain_handler'),
)

urlpatterns += main_patterns
