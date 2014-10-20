from django.conf.urls import patterns, url
from bookmarks.views import BookmarkList, bookmark_add, bookmark_remove

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'bookmarks.views',
    url(r'^$',
        BookmarkList.as_view(),
        name='user_bookmarks'),

    url(r'^add/$',
        'bookmark_add',
        name='bookmarks_add'),

    url(r'^remove/(?P<bookmark_pk>[-\w]+)/$',
        'bookmark_remove',
        name='bookmark_remove'),
)
