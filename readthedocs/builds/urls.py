"""URL configuration for builds app."""

from django.conf.urls import url
from django.views.generic.base import RedirectView


urlpatterns = [
    url(
        r'^(?P<project_slug>[-\w]+)/(?P<build_pk>\d+)/$',
        RedirectView.as_view(pattern_name='builds_detail', permanent=True),
        name='old_builds_detail',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/$',
        RedirectView.as_view(pattern_name='builds_project_list', permanent=True),
        name='old_builds_project_list',
    ),
]
