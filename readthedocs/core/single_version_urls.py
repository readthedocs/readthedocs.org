from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    # Handle /docs on RTD domain
    url(r'^docs/(?P<project_slug>[-\w]+)/(?P<filename>.*)$',
        'core.views.serve_single_version_docs',
        name='docs_detail'),

    # Handle subdomains
    url(r'^(?P<filename>.*)$',
        'core.views.serve_single_version_docs',
        name='docs_detail'),
)
