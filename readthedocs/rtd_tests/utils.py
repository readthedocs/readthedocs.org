# -*- coding: utf-8 -*-
"""Utility functions for use in tests."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import subprocess
from os import chdir, environ, mkdir
from os.path import abspath
from os.path import join as pjoin
from shutil import copytree
from tempfile import mkdtemp

from django.contrib.auth.models import User
from django_dynamic_fixture import new

from readthedocs.doc_builder.base import restoring_chdir

log = logging.getLogger(__name__)


def get_readthedocs_app_path():
    """
    Return the absolute path of the ``readthedocs`` app.
    """

    try:
        import readthedocs
        path = readthedocs.__path__[0]
    except (IndexError, ImportError):
        raise Exception('Unable to find "readthedocs" path module')

    return path


def check_output(command, env=None):
    output = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env
    ).communicate()[0]
    log.info(output)
    return output


@restoring_chdir
def make_test_git():
    directory = mkdtemp()
    directory = make_git_repo(directory)
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    # Add fake repo as submodule. We need to fake this here because local path
    # URL are not allowed and using a real URL will require Internet to clone
    # the repo
    check_output(['git', 'checkout', '-b', 'submodule', 'master'], env=env)
    # https://stackoverflow.com/a/37378302/2187091
    mkdir(pjoin(directory, 'foobar'))
    gitmodules_path = pjoin(directory, '.gitmodules')
    with open(gitmodules_path, 'w') as fh:
        fh.write('''[submodule "foobar"]\n\tpath = foobar\n\turl = https://foobar.com/git\n''')
    check_output(
        [
            'git', 'update-index', '--add', '--cacheinfo', '160000',
            '233febf4846d7a0aeb95b6c28962e06e21d13688', 'foobar',
        ],
        env=env,
    )
    check_output(['git', 'add', '.'], env=env)
    check_output(['git', 'commit', '-m"Add submodule"'], env=env)

    # Add a relative submodule URL in the relativesubmodule branch
    check_output(['git', 'checkout', '-b', 'relativesubmodule', 'master'], env=env)
    check_output(
        ['git', 'submodule', 'add', '-b', 'master', './', 'relativesubmodule'],
        env=env
    )
    check_output(['git', 'add', '.'], env=env)
    check_output(['git', 'commit', '-m"Add relative submodule"'], env=env)
    # Add an invalid submodule URL in the invalidsubmodule branch
    check_output(['git', 'checkout', '-b', 'invalidsubmodule', 'master'], env=env)
    check_output(
        ['git', 'submodule', 'add', '-b', 'master', './', 'invalidsubmodule'],
        env=env,
    )
    check_output(['git', 'add', '.'], env=env)
    check_output(['git', 'commit', '-m"Add invalid submodule"'], env=env)

    # Checkout to master branch again
    check_output(['git', 'checkout', 'master'], env=env)
    return directory


@restoring_chdir
def make_git_repo(directory, name='sample_repo'):
    path = get_readthedocs_app_path()
    sample = abspath(pjoin(path, 'rtd_tests/fixtures/sample_repo'))
    directory = pjoin(directory, name)
    copytree(sample, directory)
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    # Initialize and configure
    check_output(['git', 'init'] + [directory], env=env)
    check_output(
        ['git', 'config', 'user.email', 'dev@readthedocs.org'],
        env=env
    )
    check_output(
        ['git', 'config', 'user.name', 'Read the Docs'],
        env=env
    )

    # Set up the actual repository
    check_output(['git', 'add', '.'], env=env)
    check_output(['git', 'commit', '-m"init"'], env=env)
    return directory


@restoring_chdir
def create_git_tag(directory, tag, annotated=False):
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    command = ['git', 'tag']
    if annotated:
        command.extend(['-a', '-m', 'Some tag'])
    command.append(tag)
    check_output(command, env=env)


@restoring_chdir
def delete_git_tag(directory, tag):
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    command = ['git', 'tag', '--delete', tag]
    check_output(command, env=env)


@restoring_chdir
def create_git_branch(directory, branch):
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    command = ['git', 'branch', branch]
    check_output(command, env=env)


@restoring_chdir
def delete_git_branch(directory, branch):
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    command = ['git', 'branch', '-D', branch]
    check_output(command, env=env)


@restoring_chdir
def create_git_submodule(directory, submodule,
                         msg='Add realative submodule', branch='master'):
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    command = ['git', 'branch', '-D', branch]
    check_output(command, env=env)
    command = ['git', 'submodule', 'add', '-b', branch, './', submodule]
    check_output(command, env=env)
    check_output(['git', 'add', '.'], env=env)
    check_output(['git', 'commit', '-m', '"{}"'.format(msg)], env=env)


@restoring_chdir
def make_test_hg():
    directory = mkdtemp()
    path = get_readthedocs_app_path()
    sample = abspath(pjoin(path, 'rtd_tests/fixtures/sample_repo'))
    directory = pjoin(directory, 'sample_repo')
    copytree(sample, directory)
    chdir(directory)
    hguser = 'Test User <test-user@readthedocs.org>'
    log.info(check_output(['hg', 'init'] + [directory]))
    log.info(check_output(['hg', 'add', '.']))
    log.info(check_output(['hg', 'commit', '-u', hguser, '-m"init"']))
    return directory


def create_user(username, password, **kwargs):
    user = new(User, username=username, **kwargs)
    user.set_password(password)
    user.save()
    return user
