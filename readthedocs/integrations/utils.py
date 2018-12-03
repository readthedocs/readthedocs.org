"""Integration utility functions."""

from __future__ import division, print_function, unicode_literals

import os


def get_secret(size=64):
    """
    Get a random string of `size` bytes.

    :param size: Number of bytes
    """
    return os.urandom(size).hex()
