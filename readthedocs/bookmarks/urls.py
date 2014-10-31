from django.conf.urls import patterns, url
from bookmarks.views import BookmarkList

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'bookmarks.views',
    url(r'^$',
        BookmarkList.as_view(),
        name='bookmark_list'),

    url(r'^add/$',
        'bookmark_add',
        name='bookmarks_add'),

    url(r'^remove/(?P<bookmark_pk>[-\w]+)/$',
        'bookmark_remove',
        name='bookmark_remove'),

    url(r'^remove/$',
        'bookmark_remove',
        name='bookmark_remove_json'),
)
