from django.conf.urls.defaults import *

urlpatterns = patterns('builds.views',
    url(r'^$',
        'build_list',
        name='builds_list'
    ),
    url(r'^(?P<project_slug>[-\w]+)/(?P<pk>\d+)/$',
        'build_detail',
        name='builds_detail'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/(?P<pk>\d+)/$',
        'legacy_build_detail',
        name='legacy_builds_detail'
    ),
    url(r'^(?P<project_slug>[-\w]+)/$',
        'build_list',
        name='builds_project_list'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/$',
        'legacy_build_list',
        name='legacy_builds_project_list'
    ),
    url(r'^tag/(?P<tag>\w+)/$',
        'build_list',
        name='builds_tag_list'
    ),
)
