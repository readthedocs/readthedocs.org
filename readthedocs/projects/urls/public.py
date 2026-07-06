"""Project URLS for public users."""

from django.urls import path
from django.urls import re_path
from django.views.generic.base import RedirectView

from readthedocs.builds import views as build_views
from readthedocs.constants import pattern_opts
from readthedocs.projects.views import public
from readthedocs.projects.views.public import ProjectDetailView
from readthedocs.projects.views.public import ProjectTagIndex
from readthedocs.search.views import ProjectSearchView


# The ProjectDetailView already contains the logic for filtering and sorting
# that is missing from the function view `public.project_versions`.
project_versions_list = ProjectDetailView.as_view()

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="projects_dashboard", permanent=True),
        name="projects_dashboard_redirect",
    ),
    path(
        "tags/<slug:tag>/",
        ProjectTagIndex.as_view(),
        name="projects_tag_detail",
    ),
    # Match all URLs from projects that have an underscore in the slug,
    # and redirect them replacing the underscore with a dash (`-`).
    re_path(
        r"^(?P<invalid_project_slug>{project_slug}_{project_slug})/".format(**pattern_opts),
        public.project_redirect,
        name="project_redirect",
    ),
    path(
        "<slug:project_slug>/",
        ProjectDetailView.as_view(),
        name="projects_detail",
    ),
    path(
        "<slug:project_slug>/downloads/",
        RedirectView.as_view(pattern_name="projects_detail", permanent=False),
        name="projects_downloads",
    ),
    # NOTE: this URL is kept here only for backward compatibility to serve
    # non-html files from the dashboard. The ``name=`` is removed to avoid
    # generating an invalid URL by mistake (we should manually generate it
    # pointing to the right place: "docs.domain.org/_/downloads/")
    re_path(
        (
            r"^(?P<project_slug>{project_slug})/downloads/(?P<type_>{downloadable_type})/"
            r"(?P<version_slug>{version_slug})/$".format(**pattern_opts)
        ),
        public.ProjectDownloadMedia.as_view(),
        name="project_download_media",
    ),
    path(
        "<slug:project_slug>/badge/",
        public.project_badge,
        name="project_badge",
    ),
    path(
        "<slug:project_slug>/search/",
        ProjectSearchView.as_view(),
        name="elastic_project_search",
    ),
    path(
        "<slug:project_slug>/builds/<int:build_pk>/",
        build_views.BuildDetail.as_view(),
        name="builds_detail",
    ),
    path(
        "<slug:project_slug>/builds/",
        build_views.BuildList.as_view(),
        name="builds_project_list",
    ),
    path(
        "<slug:project_slug>/versions/",
        project_versions_list,
        name="project_version_list",
    ),
]
