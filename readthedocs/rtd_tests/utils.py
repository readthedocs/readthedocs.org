"""Utility functions for use in tests."""

from __future__ import absolute_import

import logging
import subprocess
from os import chdir, environ, getcwd, mkdir
from os.path import abspath, join as pjoin
from shutil import copytree
from tempfile import mkdtemp

from django_dynamic_fixture import new
from django.contrib.auth.models import User


log = logging.getLogger(__name__)


def check_output(l, env=()):
    if env == ():
        output = subprocess.Popen(l, stdout=subprocess.PIPE).communicate()[0]
    else:
        output = subprocess.Popen(l, stdout=subprocess.PIPE,
                                  env=env).communicate()[0]
    return output


def make_test_git():
    directory = mkdtemp()
    path = getcwd()
    sample = abspath(pjoin(path, 'rtd_tests/fixtures/sample_repo'))
    directory = pjoin(directory, 'sample_repo')
    copytree(sample, directory)
    env = environ.copy()
    env['GIT_DIR'] = pjoin(directory, '.git')
    chdir(directory)

    # Initialize and configure
    # TODO: move the ``log.info`` call inside the ``check_output```
    log.info(check_output(['git', 'init'] + [directory], env=env))
    log.info(check_output(
        ['git', 'config', 'user.email', 'dev@readthedocs.org'],
        env=env
    ))
    log.info(check_output(
        ['git', 'config', 'user.name', 'Read the Docs'],
        env=env
    ))

    # Set up the actual repository
    log.info(check_output(['git', 'add', '.'], env=env))
    log.info(check_output(['git', 'commit', '-m"init"'], env=env))

    # Add fake repo as submodule. We need to fake this here because local path
    # URL are not allowed and using a real URL will require Internet to clone
    # the repo
    log.info(check_output(['git', 'checkout', '-b', 'submodule', 'master'], env=env))
    # https://stackoverflow.com/a/37378302/2187091
    mkdir(pjoin(directory, 'foobar'))
    gitmodules_path = pjoin(directory, '.gitmodules')
    with open(gitmodules_path, 'w') as fh:
        fh.write('''[submodule "foobar"]\n\tpath = foobar\n\turl = https://foobar.com/git\n''')
    log.info(check_output(
        [
            'git', 'update-index', '--add', '--cacheinfo', '160000',
            '233febf4846d7a0aeb95b6c28962e06e21d13688', 'foobar',
        ],
        env=env,
    ))
    log.info(check_output(['git', 'add', '.'], env=env))
    log.info(check_output(['git', 'commit', '-m"Add submodule"'], env=env))

    # Add a relative submodule URL in the relativesubmodule branch
    log.info(check_output(['git', 'checkout', '-b', 'relativesubmodule', 'master'], env=env))
    log.info(check_output(
        ['git', 'submodule', 'add', '-b', 'master', './', 'relativesubmodule'],
        env=env
    ))
    log.info(check_output(['git', 'add', '.'], env=env))
    log.info(check_output(['git', 'commit', '-m"Add relative submodule"'], env=env))
    # Add an invalid submodule URL in the invalidsubmodule branch
    log.info(check_output(['git', 'checkout', '-b', 'invalidsubmodule', 'master'], env=env))
    log.info(check_output(
        ['git', 'submodule', 'add', '-b', 'master', './', 'invalidsubmodule'],
        env=env,
    ))
    log.info(check_output(['git', 'add', '.'], env=env))
    log.info(check_output(['git', 'commit', '-m"Add invalid submodule"'], env=env))

    # Checkout to master branch again
    log.info(check_output(['git', 'checkout', 'master'], env=env))
    chdir(path)
    return directory


def make_test_hg():
    directory = mkdtemp()
    path = getcwd()
    sample = abspath(pjoin(path, 'rtd_tests/fixtures/sample_repo'))
    directory = pjoin(directory, 'sample_repo')
    copytree(sample, directory)
    chdir(directory)
    hguser = 'Test User <test-user@readthedocs.org>'
    log.info(check_output(['hg', 'init'] + [directory]))
    log.info(check_output(['hg', 'add', '.']))
    log.info(check_output(['hg', 'commit', '-u', hguser, '-m"init"']))
    chdir(path)
    return directory


def create_user(username, password, **kwargs):
    user = new(User, username=username, **kwargs)
    user.set_password(password)
    user.save()
    return user
