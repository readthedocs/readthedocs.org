from django.conf.urls.defaults import *

urlpatterns = patterns('bookmarks.views',
    url(r'^$',
        'bookmark_list',
        name='bookmarks_list'
    ),
    url(r'^add/(?P<url>.*)/$',
        'bookmark_add',
        name='bookmarks_add'
    ),
    url(r'^remove/(?P<url>.*)/$',
        'bookmark_remove',
        name='bookmarks_remove'
    ),
)
