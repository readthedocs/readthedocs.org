# -*- coding: utf-8 -*-
"""Utilities for the builds app."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import re

GH_REGEXS = [
    re.compile('github.com/(.+)/(.+)(?:\.git){1}$'),
    re.compile('github.com/(.+)/(.+)'),
    re.compile('github.com:(.+)/(.+).git$'),
]

BB_REGEXS = [
    re.compile('bitbucket.org/(.+)/(.+)/'),
    re.compile('bitbucket.org/(.+)/(.+)'),
    re.compile('bitbucket.org:(.+)/(.+)\.git$'),
]

# TODO: I think this can be different than `gitlab.com`
# self.adapter.provider_base_url
GL_REGEXS = [
    re.compile('gitlab.com/(.+)/(.+)(?:\.git){1}$'),
    re.compile('gitlab.com/(.+)/(.+)'),
    re.compile('gitlab.com:(.+)/(.+)\.git$'),
]


def get_github_username_repo(url):
    if 'github' in url:
        for regex in GH_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_bitbucket_username_repo(url=None):
    if 'bitbucket' in url:
        for regex in BB_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)


def get_gitlab_username_repo(url=None):
    if 'gitlab' in url:
        for regex in GL_REGEXS:
            match = regex.search(url)
            if match:
                return match.groups()
    return (None, None)
