"""Project URLS for public users."""

from django.conf.urls import re_path
from django.views.generic.base import RedirectView

from readthedocs.builds import views as build_views
from readthedocs.constants import pattern_opts
from readthedocs.projects.views import public
from readthedocs.projects.views.public import ProjectDetailView, ProjectTagIndex
from readthedocs.search.views import ProjectSearchView

urlpatterns = [
    re_path(
        r'^$',
        RedirectView.as_view(pattern_name='projects_dashboard', permanent=True),
        name='projects_dashboard_redirect',
    ),
    re_path(
        r'^tags/(?P<tag>[-\w]+)/$',
        ProjectTagIndex.as_view(),
        name='projects_tag_detail',
    ),
    re_path(
        r'^(?P<invalid_project_slug>{project_slug}_{project_slug})/'.format(**pattern_opts),
        public.project_redirect,
        name='project_redirect',
    ),
    re_path(
        r'^(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        ProjectDetailView.as_view(),
        name='projects_detail',
    ),
    re_path(
        r'^(?P<project_slug>{project_slug})/downloads/$'.format(**pattern_opts),
        public.project_downloads,
        name='project_downloads',
    ),

    # NOTE: this URL is kept here only for backward compatibility to serve
    # non-html files from the dashboard. The ``name=`` is removed to avoid
    # generating an invalid URL by mistake (we should manually generate it
    # pointing to the right place: "docs.domain.org/_/downloads/")
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/downloads/(?P<type_>[-\w]+)/'
            r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)
        ),
        public.ProjectDownloadMedia.as_view(),
    ),

    re_path(
        r'^(?P<project_slug>{project_slug})/badge/$'.format(**pattern_opts),
        public.project_badge,
        name='project_badge',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/tools/embed/$'.format(
                **pattern_opts
            )
        ),
        public.project_embed,
        name='project_embed',
    ),
    re_path(
        r'^(?P<project_slug>{project_slug})/search/$'.format(**pattern_opts),
        ProjectSearchView.as_view(),
        name='elastic_project_search',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/builds/(?P<build_pk>\d+)/$'.format(
                **pattern_opts
            )
        ),
        build_views.BuildDetail.as_view(),
        name='builds_detail',
    ),
    re_path(
        (r'^(?P<project_slug>{project_slug})/builds/$'.format(**pattern_opts)),
        build_views.BuildList.as_view(),
        name='builds_project_list',
    ),
    re_path(
        r'^(?P<project_slug>{project_slug})/versions/$'.format(**pattern_opts),
        public.project_versions,
        name='project_version_list',
    ),
]
