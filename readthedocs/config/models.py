"""Models for the response of the configuration object."""

from __future__ import division, print_function, unicode_literals

from collections import namedtuple

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
