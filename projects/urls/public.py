from django.conf.urls.defaults import *

urlpatterns = patterns('projects.views.public',
    url(r'^$',
        'project_index',
        name='projects_list'
    ),
    url(r'^tags/$',
        'tag_index',
        name='project_tag_list',
    ),
    url(r'^tags/(?P<tag>\w+)/$',
        'project_index',
        name='project_tag_detail',
    ),
    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'
    ),
)
