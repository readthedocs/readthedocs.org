from django.conf.urls import patterns, url


urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'bookmarks.views',
    url(r'^$',
        'bookmark_list',
        name='bookmarks_list'),

    url(r'^add/(?P<url>.*)/$',
        'bookmark_add',
        name='bookmarks_add'),

    url(r'^remove/(?P<url>.*)/$',
        'bookmark_remove',
        name='bookmarks_remove'),
)
