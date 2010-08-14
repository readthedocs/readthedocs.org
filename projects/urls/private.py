from django.conf.urls.defaults import *

urlpatterns = patterns('projects.views.private',
    url(r'^$',
        'project_dashboard',
        name='projects_dashboard'
    ),
    url(r'^create/$',
        'project_create',
        name='projects_create'
    ),
    url(r'^import/$',
        'project_import',
        name='projects_import'
    ),
    url(r'^(?P<project_slug>[-\w]+)/$',
        'project_edit',
        name='projects_edit'
    ),
    url(r'^(?P<project_slug>[-\w]+)/delete/$',
        'project_delete',
        name='projects_delete'
    ),
)
