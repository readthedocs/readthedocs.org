"""Conditional classes for OAuth services"""

from django.utils.module_loading import import_by_path
from django.conf import settings

GitHubService = import_by_path(
    getattr(settings, 'OAUTH_GITHUB_SERVICE',
            'readthedocs.oauth.services.github.GitHubService'))
BitbucketService = import_by_path(
    getattr(settings, 'OAUTH_BITBUCKET_SERVICE',
            'readthedocs.oauth.services.bitbucket.BitbucketService'))

registry = [GitHubService, BitbucketService]
