"""Models for the response of the configuration object."""

from __future__ import division, print_function, unicode_literals

from collections import namedtuple


Build = namedtuple('Build', ['image'])  # noqa

Python = namedtuple(  # noqa
    'Python',
    [
        'version',
        'requirements',
        'install_with_pip',
        'install_with_setup',
        'extra_requirements',
        'use_system_site_packages',
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
