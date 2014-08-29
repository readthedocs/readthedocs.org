from django.conf.urls import patterns, url

from projects.views.public import ProjectIndex

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    '',
    url(r'^$',
        ProjectIndex.as_view(),
        name='projects_list'),

    url(r'^search/autocomplete/$',
        'projects.views.public.search_autocomplete',
        name='search_autocomplete'),

    url(r'^autocomplete/version/(?P<project_slug>[-\w]+)/$',
        'projects.views.public.version_autocomplete',
        name='version_autocomplete'),

    url(r'^autocomplete/filter/version/(?P<project_slug>[-\w]+)/$',
        'projects.views.public.version_filter_autocomplete',
        name='version_filter_autocomplete'),

    url(r'^tags/(?P<tag>[-\w]+)/$',
        ProjectIndex.as_view(),
        name='projects_tag_detail'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        'projects.views.public.project_detail',
        name='projects_detail'),

    url(r'^(?P<project_slug>[-\w]+)/downloads/$',
        'projects.views.public.project_downloads',
        name='project_downloads'),

    url(r'^(?P<project_slug>[-\w]+)/download/(?P<type>[-\w]+)/(?P<version_slug>[-\w.]+)/$',
        'projects.views.public.project_download_media',
        name='project_download_media'),

    url(r'^(?P<project_slug>[-\w]+)/badge/$',
        'projects.views.public.project_badge',
        name='project_badge'),

    url(r'^(?P<project_slug>[-\w]+)/search/$',
        'projects.views.public.elastic_project_search',
        name='elastic_project_search'),

    url(r'^(?P<project_slug>[-\w]+)/autocomplete/file/$',
        'projects.views.public.file_autocomplete',
        name='file_autocomplete'),


    url(r'^(?P<username>\w+)/$',
        'projects.views.public.project_index',
        name='projects_user_list'),
)
