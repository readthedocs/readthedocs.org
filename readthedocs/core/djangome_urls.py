from django.conf.urls.defaults import patterns, url

ALL_VERSIONS_RE = '(?P<version>.+)'

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url('^$',
        'djangome.views.redirect_home',
        {'version': 'latest'}),
    # Disable django.me integration for now.
)
