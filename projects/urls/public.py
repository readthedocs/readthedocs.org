from django.conf.urls.defaults import *

urlpatterns = patterns('projects.views.public',
    url(r'^$',
        'project_index',
        name='projects_list'
    ),
    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/$',
        'project_detail',
        name='projects_detail'
    ),
)
