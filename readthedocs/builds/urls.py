from django.conf.urls import patterns, url

from .views import BuildList, BuildDetail


urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'builds.views',
    url(r'^(?P<project_slug>[-\w]+)/(?P<pk>\d+)/$',
        BuildDetail.as_view(),
        name='builds_detail'),
    
    url(r'^(?P<project_slug>[-\w]+)/$',
        BuildList.as_view(),
        name='builds_project_list'),
)
