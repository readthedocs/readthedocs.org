"""URL patterns for views to modify user profiles."""

from django.conf.urls import url

from readthedocs.core.forms import UserProfileForm
from readthedocs.profiles import views

# Split URLs into different lists to be able to selectively import them from a
# another application (like Read the Docs Corporate), where we may don't need to
# define Token URLs, for example.
urlpatterns = []

account_urls = [
    url(
        r'^edit/',
        views.ProfileEdit.as_view(),
        name='profiles_profile_edit',
    ),
    url(
        r'^delete/',
        views.AccountDelete.as_view(),
        name='delete_account',
    ),
    url(
        r'^advertising/$',
        views.AccountAdvertisingEdit.as_view(),
        name='account_advertising',
    ),
]

urlpatterns += account_urls

tokens_urls = [
    url(
        r'^tokens/$',
        views.TokenListView.as_view(),
        name='profiles_tokens',
    ),
    url(
        r'^tokens/create/$',
        views.TokenCreateView.as_view(),
        name='profiles_tokens_create',
    ),
    url(
        r'^tokens/delete/$',
        views.TokenDeleteView.as_view(),
        name='profiles_tokens_delete',
    ),
]

urlpatterns += tokens_urls
