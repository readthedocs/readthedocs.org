"""Gold subscription URLs"""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.gold import views
from readthedocs.projects.constants import PROJECT_SLUG_REGEX


urlpatterns = [
    url(r'^$', views.DetailGoldSubscription.as_view(), name='gold_detail'),
    url(r'^subscription/$', views.UpdateGoldSubscription.as_view(),
        name='gold_subscription'),
    url(r'^cancel/$', views.DeleteGoldSubscription.as_view(), name='gold_cancel'),
    url(r'^projects/$', views.projects, name='gold_projects'),
    url((r'^projects/remove/(?P<project_slug>{project_slug})/$'
         .format(project_slug=PROJECT_SLUG_REGEX)),
        views.projects_remove,
        name='gold_projects_remove'),
]
