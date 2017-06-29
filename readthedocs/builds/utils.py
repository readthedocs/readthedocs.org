"""Utilities for the builds app."""

from __future__ import absolute_import
import re


GH_REGEXS = [
    re.compile('github.com/(.+)/(.+)(?:\.git){1}'),
    re.compile('github.com/(.+)/(.+)'),
    re.compile('github.com:(.+)/(.+).git'),
]

BB_REGEXS = [
    re.compile('bitbucket.org/(.+)/(.+)/'),
    re.compile('bitbucket.org/(.+)/(.+)'),
    re.compile('bitbucket.org:(.+)/(.+)\.git'),
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
