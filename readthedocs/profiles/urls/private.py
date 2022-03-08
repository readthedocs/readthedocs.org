"""URL patterns for views to modify user profiles."""

from django.conf.urls import re_path

from readthedocs.profiles import views

# Split URLs into different lists to be able to selectively import them from a
# another application (like Read the Docs Corporate), where we may don't need to
# define Token URLs, for example.
urlpatterns = []

account_urls = [
    re_path(
        r'^login',
        views.LoginView.as_view(),
        name='account_login',
    ),
    re_path(
        r'^logout/',
        views.LogoutView.as_view(),
        name='account_logout',
    ),
    re_path(
        r'^edit/',
        views.ProfileEdit.as_view(),
        name='profiles_profile_edit',
    ),
    re_path(
        r'^delete/',
        views.AccountDelete.as_view(),
        name='delete_account',
    ),
    re_path(
        r'security-log/',
        views.UserSecurityLogView.as_view(),
        name='profiles_security_log',
    ),
    re_path(
        r'^advertising/$',
        views.AccountAdvertisingEdit.as_view(),
        name='account_advertising',
    ),
]

urlpatterns += account_urls

tokens_urls = [
    re_path(
        r'^tokens/$',
        views.TokenListView.as_view(),
        name='profiles_tokens',
    ),
    re_path(
        r'^tokens/create/$',
        views.TokenCreateView.as_view(),
        name='profiles_tokens_create',
    ),
    re_path(
        r'^tokens/delete/$',
        views.TokenDeleteView.as_view(),
        name='profiles_tokens_delete',
    ),
]

urlpatterns += tokens_urls
