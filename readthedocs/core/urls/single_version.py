from django.conf.urls import patterns, url

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    # Handle /docs on RTD domain
    url(r'^docs/(?P<project_slug>[-\w]+)/(?P<filename>.*)$',
        'readthedocs.core.views.serve.serve_symlink_docs',
        name='docs_detail'),

    # Handle subdomains
    url(r'^(?P<filename>.*)$',
        'readthedocs.core.views.serve.serve_symlink_docs',
        name='docs_detail'),
)
