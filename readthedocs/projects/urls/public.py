"""Project URLS for public users"""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.projects.views import public
from readthedocs.projects.views.public import ProjectIndex, ProjectDetailView

from readthedocs.builds import views as build_views
from readthedocs.constants import pattern_opts


urlpatterns = [
    url(r'^$',
        ProjectIndex.as_view(),
        name='projects_list'),

    url(r'^search/autocomplete/$',
        public.search_autocomplete,
        name='search_autocomplete'),

    url(r'^autocomplete/version/(?P<project_slug>[-\w]+)/$',
        public.version_autocomplete,
        name='version_autocomplete'),

    url(r'^(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        ProjectDetailView.as_view(),
        name='projects_detail'),

    url(r'^(?P<project_slug>{project_slug})/downloads/$'.format(**pattern_opts),
        public.project_downloads,
        name='project_downloads'),

    url((r'^(?P<project_slug>{project_slug})/downloads/(?P<type_>[-\w]+)/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        public.project_download_media,
        name='project_download_media'),

    url(r'^(?P<project_slug>{project_slug})/badge/$'.format(**pattern_opts),
        public.project_badge,
        name='project_badge'),

    url((r'^(?P<project_slug>{project_slug})/tools/embed/$'
         .format(**pattern_opts)),
        public.project_embed,
        name='project_embed'),

    url(r'^(?P<project_slug>{project_slug})/search/$'.format(**pattern_opts),
        public.elastic_project_search,
        name='elastic_project_search'),

    url((r'^(?P<project_slug>{project_slug})/builds/(?P<build_pk>\d+)/$'
         .format(**pattern_opts)),
        build_views.BuildDetail.as_view(),
        name='builds_detail'),

    url((r'^(?P<project_slug>{project_slug})/builds/$'
         .format(**pattern_opts)),
        build_views.BuildList.as_view(),
        name='builds_project_list'),

    url((r'^(?P<project_slug>{project_slug})/autocomplete/file/$'
         .format(**pattern_opts)),
        public.file_autocomplete,
        name='file_autocomplete'),

    url(r'^(?P<project_slug>{project_slug})/versions/$'.format(**pattern_opts),
        public.project_versions,
        name='project_version_list'),

    url(r'^tags/(?P<tag>[-\w]+)/$',
        ProjectIndex.as_view(),
        name='projects_tag_detail'),
]
