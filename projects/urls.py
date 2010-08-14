from django.conf.urls.defaults import *

urlpatterns = patterns('projects.views',
    url(r'^$',
        'project_index',
        name='projects_list'
    ),
    url(r'^create/$',
        'project_create',
        name='projects_create'
    ),
    url(r'^import/$',
        'project_import',
        name='projects_import'
    ),
    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/$',
        'project_detail',
        name='projects_detail'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/edit/$',
        'project_edit',
        name='projects_edit'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/delete/$',
        'project_delete',
        name='projects_delete'
    ),
)
