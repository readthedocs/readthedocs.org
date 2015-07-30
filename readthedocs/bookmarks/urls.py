from django.conf.urls import patterns, url
from readthedocs.bookmarks.views import BookmarkListView
from readthedocs.bookmarks.views import BookmarkAddView, BookmarkRemoveView
from readthedocs.bookmarks.views import BookmarkExistsView

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'readthedocs.bookmarks.views',
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
)
