from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'projects.views.public',
    url(r'^$',
        'project_index',
        name='projects_list'),

    url(r'^tags/$',
        'tag_index',
        name='projects_tag_list'),

    url(r'^search/$',
        'search',
        name='project_search'),

    url(r'^search/autocomplete/$',
        'search_autocomplete',
        name='search_autocomplete'),

    url(r'^autocomplete/version/(?P<project_slug>[-\w]+)/$',
        'version_autocomplete',
        name='version_autocomplete'),

    url(r'^autocomplete/filter/version/(?P<project_slug>[-\w]+)/$',
        'version_filter_autocomplete',
        name='version_filter_autocomplete'),

    url(r'^tags/(?P<tag>[-\w]+)/$',
        'project_index',
        name='projects_tag_detail'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        'project_detail',
        name='projects_detail'),

    url(r'^(?P<project_slug>[-\w]+)/downloads/$',
        'project_downloads',
        name='project_downloads'),

    url(r'^(?P<project_slug>[-\w]+)/badge/$',
        'project_badge',
        name='project_badge'),

    url(r'^(?P<username>\w+)/$',
        'project_index',
        name='projects_user_list'),
)
