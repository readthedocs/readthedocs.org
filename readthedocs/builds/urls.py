"""URL configuration for builds app."""

from __future__ import absolute_import
from django.conf.urls import url

from .views import builds_redirect_detail, builds_redirect_list


urlpatterns = [
    url(r'^(?P<project_slug>[-\w]+)/(?P<pk>\d+)/$',
        builds_redirect_detail,
        name='old_builds_detail'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        builds_redirect_list,
        name='old_builds_project_list'),
]
