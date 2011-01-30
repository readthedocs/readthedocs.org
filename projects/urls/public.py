from django.conf.urls.defaults import *

urlpatterns = patterns('projects.views.public',
    url(r'^$',
        'project_index',
        name='projects_list'
    ),
    url(r'^tags/$',
        'tag_index',
        name='projects_tag_list',
    ),
    url(r'^search/$',
        'search',
        name='search',
    ),
    url(r'^search/autocomplete/$',
        'search_autocomplete',
        name='search_autocomplete',
    ),
    url(r'^tags/(?P<tag>[-\w]+)/$',
        'project_index',
        name='projects_tag_detail',
    ),
    url(r'^(?P<project_slug>[-\w]+)/$',
        'project_detail',
        name='projects_detail'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/$',
        'legacy_project_detail',
        name='legacy_projects_detail'
    ),
    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'
    ),
)

urlpatterns += patterns('',
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/docs/(?P<filename>.*)$',
        'core.views.legacy_serve_docs',
    ),
)
