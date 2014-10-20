from django.conf.urls import patterns, url


urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'bookmarks.views',
    url(r'^$',
        BookmarkList.as_view(),
        name='user_bookmarks'),

    url(r'^add/$',
        'bookmark_add',
        name='bookmarks_add'),

    url(r'^remove/$',
        'bookmark_remove',
        name='bookmarks_remove'),
)
