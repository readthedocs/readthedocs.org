"""Conditional classes for OAuth services"""

from __future__ import absolute_import
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.oauth.services import github, bitbucket


class GitHubService(SettingsOverrideObject):
    _default_class = github.GitHubService
    _override_setting = 'OAUTH_GITHUB_SERVICE'


class BitbucketService(SettingsOverrideObject):
    _default_class = bitbucket.BitbucketService
    _override_setting = 'OAUTH_BITBUCKET_SERVICE'


registry = [GitHubService, BitbucketService]
