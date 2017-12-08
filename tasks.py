# -*- coding: utf-8 -*-
"""Read the Docs invoke tasks."""

from __future__ import division, print_function, unicode_literals

import os
import textwrap

from future.moves.configparser import RawConfigParser
from invoke import task


@task
def prepare(ctx, version):
    """
    Prepare the next release version by updating files.

    This will stage a few updates for manual review and commit:

    * Prepend the most recent PRs and issues that were closed to CHANGELOG.rst.
    * Update the setup.cfg version

    Changelog uses the file modification date to track the last time it was
    updated.  New entries will end up at the top of the file, under a heading
    for the new version.
    """
    print('Updating release version in setup.cfg')
    setupcfg_path = os.path.join(os.path.dirname(__file__), 'setup.cfg')
    config = RawConfigParser()
    config.read(setupcfg_path)
    config.set('metadata', 'version', version)
    with open(setupcfg_path, 'wb') as configfile:
        config.write(configfile)

    print('Installing github-changelog')
    ctx.run('npm install git+https://github.com/agjohnson/github-changelog.git')
    changelog_path = os.path.join(os.path.dirname(__file__), 'CHANGELOG.rst')
    template_path = os.path.join(
        os.path.dirname(__file__),
        'contrib',
        'changelog.hbs',
    )
    cmd = (
        'gh-changelog '
        '-o rtfd -r readthedocs.org '
        '--file {changelog_path} '
        '--template {template_path} '
        '--header "Version {version}"'
    ).format(
        version=version,
        template_path=template_path,
        changelog_path=changelog_path,
    )  # yapf: disable
    try:
        token = os.environ['GITHUB_TOKEN']
        cmd += '--token ' + token + ' '
    except KeyError:
        print('')
        print(
            '\n'.join(
                textwrap.wrap(
                    'In order to avoid rate limiting on the GitHub API, you can specify '
                    'an environment variable `GITHUB_TOKEN` with a personal access token. '
                    'There is no need for the token to have any permissions unless the '
                    'repoistory is private.')))
        print('')
    print('Updating changelog')
    ctx.run(cmd)


@task
def release(ctx, version):
    """
    Tag release of Read the Docs.

    Do this after prepare task and manual cleanup/commit
    """
    ctx.run(
        ('git checkout master && '
         'git tag {version} && '
         'git push --tags').format(version=version))
