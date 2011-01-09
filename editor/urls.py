from django.conf.urls.defaults import *

urlpatterns = patterns('editor.views',
    url(r'^(?P<project_slug>[-\w]+)/pick/$',
        'editor_pick',
        name='editor_pick'
    ),
    url(r'^(?P<project_slug>[-\w]+)/file/(?P<filename>.*)$',
        'editor_file',
        name='editor_file'
    ),
    url(r'^push/(?P<project_slug>[-\w]+)/$',
        'editor_push',
        name='editor_push'
    ),
)