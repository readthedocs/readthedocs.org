# -*- coding: utf-8 -*-

"""Utilities for the builds app."""

from readthedocs.projects.constants import (
    BITBUCKET_REGEXS,
    GITHUB_REGEXS,
    GITLAB_REGEXS,
)


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
