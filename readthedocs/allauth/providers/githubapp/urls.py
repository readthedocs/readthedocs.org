"""Copied from allauth.socialaccount.providers.github.urls."""

from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider


urlpatterns = default_urlpatterns(GitHubAppProvider)
