from django.conf.urls import url, patterns, include

from readthedocs.gold import views
from readthedocs.projects.constants import PROJECT_SLUG_REGEX


urlpatterns = patterns('',
                       url(r'^register/$', views.register, name='gold_register'),
                       url(r'^edit/$', views.edit, name='gold_edit'),
                       url(r'^cancel/$', views.cancel, name='gold_cancel'),
                       url(r'^thanks/$', views.thanks, name='gold_thanks'),
                       url(r'^projects/$', views.projects, name='gold_projects'),
                       url(r'^projects/remove/(?P<project_slug>{project_slug})/$'.format(
                           project_slug=PROJECT_SLUG_REGEX
                       ),
                           views.projects_remove,
                           name='gold_projects_remove'),
                       )
