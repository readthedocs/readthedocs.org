"""URL patterns for views to modify user profiles."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from django.conf.urls import url

from readthedocs.core.forms import UserProfileForm
from readthedocs.profiles import views


urlpatterns = [
    url(
        r'^edit/', views.edit_profile,
        {
            'form_class': UserProfileForm,
            'template_name': 'profiles/private/edit_profile.html',
        },
        name='profiles_profile_edit'
    ),
    url(r'^delete/', views.delete_account, name='delete_account'),
    url(
        r'^advertising/$',
        views.account_advertising,
        name='account_advertising',
    ),
]
