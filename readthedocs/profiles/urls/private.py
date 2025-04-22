"""URL patterns for views to modify user profiles."""

from django.urls import path

from readthedocs.profiles import views


# Split URLs into different lists to be able to selectively import them from a
# another application (like Read the Docs Corporate), where we may don't need to
# define Token URLs, for example.
urlpatterns = []

account_urls = [
    path(
        "login/",
        views.LoginView.as_view(),
        name="account_login",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="account_logout",
    ),
    path(
        "edit/",
        views.ProfileEdit.as_view(),
        name="profiles_profile_edit",
    ),
    path(
        "delete/",
        views.AccountDelete.as_view(),
        name="delete_account",
    ),
    path(
        "security-log/",
        views.UserSecurityLogView.as_view(),
        name="profiles_security_log",
    ),
    path(
        "advertising/",
        views.AccountAdvertisingEdit.as_view(),
        name="account_advertising",
    ),
    path(
        "migrate-to-github-app/",
        views.MigrateToGitHubAppView.as_view(),
        name="migrate_to_github_app",
    ),
]

urlpatterns += account_urls

tokens_urls = [
    path(
        "tokens/",
        views.TokenListView.as_view(),
        name="profiles_tokens",
    ),
    path(
        "tokens/create/",
        views.TokenCreateView.as_view(),
        name="profiles_tokens_create",
    ),
    path(
        "tokens/delete/",
        views.TokenDeleteView.as_view(),
        name="profiles_tokens_delete",
    ),
]

urlpatterns += tokens_urls
