"""URL patterns to view user profiles."""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.profiles import views


urlpatterns = [
    url(r'^(?P<username>[\w@.-]+)/$',
        views.profile_detail,
        {'template_name': 'profiles/public/profile_detail.html'},
        name='profiles_profile_detail'),
]
