"""Models for the response of the configuration object."""

from __future__ import division, print_function, unicode_literals

from collections import namedtuple


Build = namedtuple('Build', ['image'])  # noqa

Python = namedtuple(  # noqa
    'Python',
    [
        'version',
        'install',
        'use_system_site_packages',
    ],
)

PythonInstallRequirements = namedtuple(
    'PythonInstallRequirements',
    [
        'requirements',
    ],
)

PythonInstall = namedtuple(
    'PythonInstall',
    [
        'path',
        'method',
        'extra_requirements',
    ],
)

Conda = namedtuple('Conda', ['environment'])  # noqa

Sphinx = namedtuple(  # noqa
    'Sphinx',
    ['builder', 'configuration', 'fail_on_warning'],
)

Mkdocs = namedtuple(  # noqa
    'Mkdocs',
    ['configuration', 'fail_on_warning'],
)

Submodules = namedtuple(  # noqa
    'Submodules',
    ['include', 'exclude', 'recursive'],
)
