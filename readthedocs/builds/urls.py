"""URL configuration for builds app."""

from django.urls import re_path
from django.views.generic.base import RedirectView


urlpatterns = [
    re_path(
        r"^(?P<project_slug>[-\w]+)/(?P<build_pk>\d+)/$",
        RedirectView.as_view(pattern_name="builds_detail", permanent=True),
        name="old_builds_detail",
    ),
    re_path(
        r"^(?P<project_slug>[-\w]+)/$",
        RedirectView.as_view(pattern_name="builds_project_list", permanent=True),
        name="old_builds_project_list",
    ),
]
