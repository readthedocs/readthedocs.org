from django.conf.urls import patterns, url

from .views import BuildList, BuildDetail


urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'readthedocs.builds.views',
    url(r'^(?P<project_slug>[-\w]+)/(?P<pk>\d+)/$',
        'builds_redirect_detail',
        name='old_builds_detail'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        'builds_redirect_list',
        name='old_builds_project_list'),
)
