from django.conf.urls import patterns, url

from readthedocs.projects.views.public import ProjectIndex, ProjectDetailView

from readthedocs.builds import views as build_views
from readthedocs.constants import pattern_opts

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    '',
    url(r'^$',
        ProjectIndex.as_view(),
        name='projects_list'),

    url(r'^search/autocomplete/$',
        'readthedocs.projects.views.public.search_autocomplete',
        name='search_autocomplete'),

    url(r'^autocomplete/version/(?P<project_slug>[-\w]+)/$',
        'readthedocs.projects.views.public.version_autocomplete',
        name='version_autocomplete'),

    url(r'^(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        ProjectDetailView.as_view(),
        name='projects_detail'),

    url(r'^(?P<project_slug>{project_slug})/downloads/$'.format(**pattern_opts),
        'readthedocs.projects.views.public.project_downloads',
        name='project_downloads'),

    url((r'^(?P<project_slug>{project_slug})/downloads/(?P<type>[-\w]+)/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        'readthedocs.projects.views.public.project_download_media',
        name='project_download_media'),

    url(r'^(?P<project_slug>{project_slug})/badge/$'.format(**pattern_opts),
        'readthedocs.projects.views.public.project_badge',
        name='project_badge'),

    url((r'^(?P<project_slug>{project_slug})/tools/embed/$'
         .format(**pattern_opts)),
        'readthedocs.projects.views.public.project_embed',
        name='project_embed'),

    url(r'^(?P<project_slug>{project_slug})/search/$'.format(**pattern_opts),
        'readthedocs.projects.views.public.elastic_project_search',
        name='elastic_project_search'),

    url((r'^(?P<project_slug>{project_slug})/builds/(?P<pk>\d+)/$'
         .format(**pattern_opts)),
        build_views.BuildDetail.as_view(),
        name='builds_detail'),

    url((r'^(?P<project_slug>{project_slug})/builds/$'
         .format(**pattern_opts)),
        build_views.BuildList.as_view(),
        name='builds_project_list'),

    url((r'^(?P<project_slug>{project_slug})/autocomplete/file/$'
         .format(**pattern_opts)),
        'readthedocs.projects.views.public.file_autocomplete',
        name='file_autocomplete'),

    url(r'^(?P<project_slug>{project_slug})/versions/$'.format(**pattern_opts),
        'readthedocs.projects.views.public.project_versions',
        name='project_version_list'),

    url(r'^tags/(?P<tag>[-\w]+)/$',
        ProjectIndex.as_view(),
        name='projects_tag_detail'),

)
