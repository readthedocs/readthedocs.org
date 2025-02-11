from allauth.socialaccount.providers.github.provider import GitHubProvider

from readthedocs.allauth.providers.githubapp.views import GitHubAppOAuth2Adapter


class GitHubAppProvider(GitHubProvider):
    """
    Provider for GitHub App.

    We subclass the GitHubProvider to so we have two separate providers for GitHub and GitHub App.
    """

    id = "githubapp"
    name = "GitHub App"
    oauth2_adapter_class = GitHubAppOAuth2Adapter


provider_classes = [GitHubAppProvider]
