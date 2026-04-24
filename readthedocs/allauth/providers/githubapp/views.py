"""Copied from allauth.socialaccount.providers.github.views."""

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView


class GitHubAppOAuth2Adapter(GitHubOAuth2Adapter):
    provider_id = "githubapp"


oauth2_login = OAuth2LoginView.adapter_view(GitHubAppOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(GitHubAppOAuth2Adapter)
