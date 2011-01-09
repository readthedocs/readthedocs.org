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
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/$',
        'project_detail',
        name='projects_detail'
    ),
    url(r'^slug/(?P<project_slug>[-\w]+)/(?P<filename>.*)$',
        'slug_detail',
        name='slug_detail'
    ),
    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/pdf/$',
        'project_pdf',
        name='projects_pdf'
    ),
)

urlpatterns += patterns('',
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/docs/(?P<filename>.*)$',
        'core.views.legacy_serve_docs',
    ),
)