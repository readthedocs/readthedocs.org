"""URL configuration for builds app."""

from django.urls import path
from django.views.generic.base import RedirectView


urlpatterns = [
    path(
        "<slug:project_slug>/<int:build_pk>/",
        RedirectView.as_view(pattern_name="builds_detail", permanent=True),
        name="old_builds_detail",
    ),
    path(
        "<slug:project_slug>/",
        RedirectView.as_view(pattern_name="builds_project_list", permanent=True),
        name="old_builds_project_list",
    ),
]
