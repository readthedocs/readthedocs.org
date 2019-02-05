# -*- coding: utf-8 -*-

"""URL patterns to view user profiles."""

from django.conf.urls import url

from readthedocs.profiles import views


urlpatterns = [
    url(
        r'^(?P<username>[+\w@.-]+)/$',
        views.profile_detail,
        {'template_name': 'profiles/public/profile_detail.html'},
        name='profiles_profile_detail',
    ),
]
