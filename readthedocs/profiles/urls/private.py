"""URL patterns for views to modify user profiles."""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.core.forms import UserProfileForm
from readthedocs.profiles import views

urlpatterns = [
    url(r'^create/', views.create_profile,
        {
            'form_class': UserProfileForm,
        },
        name='profiles_profile_create'),
    url(r'^edit/', views.edit_profile,
        {
            'form_class': UserProfileForm,
            'template_name': 'profiles/private/edit_profile.html',
        },
        name='profiles_profile_edit'),
]
