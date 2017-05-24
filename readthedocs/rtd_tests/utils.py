"""Utility functions for use in tests."""
import logging
from os import chdir, environ, getcwd
from os.path import abspath, join as pjoin
from shutil import copytree
import subprocess
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
    log.info(check_output(['git', 'init'] + [directory], env=env))
    log.info(check_output(['git', 'add', '.'], env=env))
    log.info(check_output(['git', 'commit', '-m"init"'], env=env))
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
