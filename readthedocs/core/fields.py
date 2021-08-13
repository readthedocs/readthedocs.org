# -*- coding: utf-8 -*-

"""Shared model fields and defaults."""

import binascii
import os


def default_token():
    """Generate default value for token field."""
    return binascii.hexlify(os.urandom(20)).decode()
