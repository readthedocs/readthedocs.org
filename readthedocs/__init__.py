# -*- coding: utf-8 -*-
"""Read the Docs."""

import os.path

from future.moves.configparser import RawConfigParser

# Import the Celery application before anything else happens
from readthedocs.worker import app  # noqa


def get_version():
    """Return package version from setup.cfg."""
    setupcfg_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'setup.cfg'),
    )
    config = RawConfigParser()
    config.read(setupcfg_path)
    return config.get('metadata', 'version')


__version__ = get_version()
