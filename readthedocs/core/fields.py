"""Shared model fields and defaults"""

import sys
from random import randrange

from django.utils.http import int_to_base36


def default_token():
    """Generate default value for token field"""
    return ''.join([int_to_base36(randrange(sys.maxint)) for _ in range(2)])
