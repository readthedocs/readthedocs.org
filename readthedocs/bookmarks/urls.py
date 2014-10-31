from django.conf.urls import patterns, url
from bookmarks.views import BookmarkListView
from bookmarks.views import BookmarkAddView, BookmarkRemoveView

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'bookmarks.views',
    url(r'^$',
        BookmarkListView.as_view(),
        name='bookmark_list'),

    url(r'^add/$',
        BookmarkAddView.as_view(),
        name='bookmarks_add'),

    url(r'^remove/(?P<bookmark_pk>[-\w]+)/$',
        BookmarkRemoveView.as_view(),
        name='bookmark_remove'),

    url(r'^remove/$',
        BookmarkRemoveView.as_view(),
        name='bookmark_remove_json'),
)
