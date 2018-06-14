from fabric.api import lcd, local
from fabric.decorators import runs_once

import os

fabfile_dir = os.path.dirname(__file__)


def i18n_push_source():
    """rebuild and push the source language to transifex"""
    with lcd('readthedocs'):
        local('rm -rf rtd_tests/tests/builds/')
        local('django-admin makemessages -l en')
        local('tx push -s')
        local('django-admin compilemessages -l en')


def i18n_pull():
    """pull the updated translation from transifex"""
    with lcd('readthedocs'):
        local('rm -rf rtd_tests/tests/builds/')
        local('tx pull -f ')
        local('django-admin makemessages --all')
        local('django-admin compilemessages')


def i18n_docs():
    with lcd('docs'):
        # Update our tanslations
        local('tx pull -a')
        local('sphinx-intl build')
        # Push new ones
        local('make gettext')
        local('tx push -s')


@runs_once
def spider():
    local('patu.py -d1 readthedocs.org')
