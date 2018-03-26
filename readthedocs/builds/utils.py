# -*- coding: utf-8 -*-
"""Utilities for the builds app."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import re

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from six.moves import urllib

from readthedocs.projects.constants import BITBUCKET_REGEXS, GITHUB_REGEX_BASES, GITLAB_REGEXS

_GITHUB_NO_PROTOCOL = urllib.parse.urlparse(GitHubOAuth2Adapter.web_url).netloc
GITHUB_REGEXS = [re.compile(b.format(re.escape(_GITHUB_NO_PROTOCOL))) for b in GITHUB_REGEX_BASES]


def get_github_username_repo(url):
    if 'github' in url:
        for regex in GITHUB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if 'bitbucket' in url:
        for regex in BITBUCKET_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_gitlab_username_repo(url=None):
    if 'gitlab' in url:
        for regex in GITLAB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)
