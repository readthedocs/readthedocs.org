# -*- coding: utf-8 -*-

"""Conditional classes for OAuth services."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.oauth.services import bitbucket, github, gitlab


class GitHubService(SettingsOverrideObject):
    _default_class = github.GitHubService
    _override_setting = 'OAUTH_GITHUB_SERVICE'


class BitbucketService(SettingsOverrideObject):
    _default_class = bitbucket.BitbucketService
    _override_setting = 'OAUTH_BITBUCKET_SERVICE'


class GitLabService(SettingsOverrideObject):
    _default_class = gitlab.GitLabService
    _override_setting = 'OAUTH_GITLAB_SERVICE'


registry = [GitHubService, BitbucketService, GitLabService]
