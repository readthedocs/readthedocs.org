from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    # Handle /docs on RTD domain
    url(r'^docs/(?P<project_slug>[-\w]+)/(?P<filename>.*)$',
        'readthedocs.core.views.serve_symlink_docs',
        name='docs_detail'),

    # Handle subdomains
    url(r'^(?P<filename>.*)$',
        'readthedocs.core.views.serve_symlink_docs',
        name='docs_detail'),
)
