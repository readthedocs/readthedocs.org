from django.conf.urls.defaults import *

urlpatterns = patterns('builds.views',
    url(r'^$',
        'build_list',
        name='build_list'
    ),
    url(r'^(?P<username>\w+)/(?P<project_slug>[-\w]+)/(?P<pk>\d+)$',
        'build_detail',
        name='build_detail'
    ),
)
