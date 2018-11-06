# -*- coding: utf-8 -*-
"""Read the Docs."""

import os.path

from future.moves.configparser import RawConfigParser


def get_version(setupcfg_path):
    """Return package version from setup.cfg."""
    config = RawConfigParser()
    config.read(setupcfg_path)
    return config.get('metadata', 'version')


__version__ = get_version(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'setup.cfg'),
    ),
)
