"""URL config for the bookmarks app."""

from __future__ import absolute_import
from django.conf.urls import url
from readthedocs.bookmarks.views import BookmarkListView
from readthedocs.bookmarks.views import BookmarkAddView, BookmarkRemoveView
from readthedocs.bookmarks.views import BookmarkExistsView

urlpatterns = [
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

    url(r'^exists/$',
        BookmarkExistsView.as_view(),
        name='bookmark_exists'),
]
