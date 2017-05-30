"""Shared model fields and defaults"""

from __future__ import absolute_import
import binascii
import os


def default_token():
    """Generate default value for token field"""
    return binascii.hexlify(os.urandom(20)).decode()
