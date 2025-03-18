from allauth.socialaccount.providers.github.provider import GitHubProvider

from readthedocs.allauth.providers.githubapp.views import GitHubAppOAuth2Adapter


class GitHubAppProvider(GitHubProvider):
    """
    Provider for GitHub App.

    We subclass the GitHubProvider to have two separate providers for the GitHub OAuth App and the GitHub App.
    """

    id = "githubapp"
    oauth2_adapter_class = GitHubAppOAuth2Adapter


provider_classes = [GitHubAppProvider]
