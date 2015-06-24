from django.conf.urls import patterns, url
from builds.constants import LATEST


urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url('^$',
        'djangome.views.redirect_home',
        {'version': LATEST}),
)
