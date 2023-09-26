"""URL patterns to view user profiles."""

from django.urls import re_path

from readthedocs.profiles import views


urlpatterns = [
    re_path(
        r"^(?P<username>[+\w@.-]+)/$",
        views.ProfileDetail.as_view(),
        name="profiles_profile_detail",
    ),
]
