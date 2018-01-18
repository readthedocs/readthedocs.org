from fabric.api import lcd, local
from fabric.decorators import runs_once

import os

fabfile_dir = os.path.dirname(__file__)


def i18n():
    with lcd('readthedocs'):
        local('rm -rf rtd_tests/tests/builds/')
        local('tx pull')
        local('django-admin makemessages --all')
        local('tx push -s')
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
