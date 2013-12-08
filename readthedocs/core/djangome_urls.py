from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url('^$',
        'djangome.views.redirect_home',
        {'version': 'latest'}),
)
