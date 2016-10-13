"""Conditional classes for OAuth services"""

from django.utils.module_loading import import_string
from django.conf import settings

GitHubService = import_string(
    getattr(settings, 'OAUTH_GITHUB_SERVICE',
            'readthedocs.oauth.services.github.GitHubService'))
BitbucketService = import_string(
    getattr(settings, 'OAUTH_BITBUCKET_SERVICE',
            'readthedocs.oauth.services.bitbucket.BitbucketService'))

registry = [GitHubService, BitbucketService]
