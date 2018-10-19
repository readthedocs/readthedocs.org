"""Models for the response of the configuration object."""

from __future__ import division, print_function, unicode_literals

from collections import namedtuple


Build = namedtuple('Build', ['image'])

Python = namedtuple(
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

PythonInstallPipfile = namedtuple(
    'PythonInstallPipfile',
    [
        'pipfile',
        'dev',
        'ignore_pipfile',
        'skip_lock',
    ]
)

Conda = namedtuple('Conda', ['environment'])

Sphinx = namedtuple(
    'Sphinx',
    ['builder', 'configuration', 'fail_on_warning'],
)

Mkdocs = namedtuple(
    'Mkdocs',
    ['configuration', 'fail_on_warning'],
)

Submodules = namedtuple(
    'Submodules',
    ['include', 'exclude', 'recursive'],
)
