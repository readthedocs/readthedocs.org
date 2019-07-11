#!/usr/bin/env python

import argparse
import json
import os
import re
import sys

import git
from git.exc import InvalidGitRepositoryError


def main():
    parser = get_parser()
    args = parser.parse_args()

    if not args.path:
        parser.print_help()
        sys.exit(1)

    try:
        repo_info = get_repo_info(args.path)
        print(json.dumps(repo_info))
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def get_parser():
    parser = argparse.ArgumentParser(
        description=(
            'Print to stdout information about a git repository '
            'in json format.'
        )
    )
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default=None,
        help='The path to a git repository.',
    )
    return parser


def get_repo_info(repo_path):
    try:
        repo = git.Repo(repo_path)
        info = {
            'commit': get_commit(repo),
            'branches': get_branches(repo),
            'tags': get_tags(repo),
            'submodules': get_submodules(repo),
        }
        return info
    except InvalidGitRepositoryError:
        raise Exception('Not repo found')


def get_commit(repo):
    return str(repo.head.commit)


def get_branches(repo):
    """Get branches from the origin remote."""

    if not repo.remotes:
        return []

    branches = []
    for branch in repo.remotes.origin.refs:
        name = branch.name
        name = re.sub('^origin/', '', name)
        if name == 'HEAD':
            continue
        branches.append(
            {
                'name': name,
                'indentifier': str(branch),
            },
        )
    return branches


def get_tags(repo):
    tags = []
    for tag in repo.tags:
        try:
            tags.append(
                {
                    'name': str(tag),
                    'identifier': str(tag.commit), 
                },
            )
        except ValueError:
            # ValueError: Cannot resolve commit as tag TAGNAME points to a
            # blob object - use the `.object` property instead to access it
            # This is not a real tag for us, so we skip it
            # https://github.com/rtfd/readthedocs.org/issues/4440
            continue
    return tags


def get_submodules(repo):
    try:
        submodules = [
            {
                'path': sub.path,
                'url': sub.url,
            }
            for sub in repo.submodules
        ]
        return submodules
    except InvalidGitRepositoryError:
        raise Exception('Invalid submodule')


if __name__ == "__main__":
    main()
