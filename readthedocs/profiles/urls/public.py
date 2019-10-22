"""URL patterns to view user profiles."""

from django.conf.urls import url

from readthedocs.profiles import views


urlpatterns = [
    url(
        r'^(?P<username>[+\w@.-]+)/$',
        views.ProfileDetail.as_view(),
        name='profiles_profile_detail',
    ),
]
