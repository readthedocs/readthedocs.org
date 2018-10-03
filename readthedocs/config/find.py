"""Helper functions to search files."""

from __future__ import division, print_function, unicode_literals

import os
import re


def find_all(path, filename_regex):
    """Find all files in ``path`` that match ``filename_regex`` regex."""
    path = os.path.abspath(path)
    for filename in os.listdir(path):
        if re.match(filename_regex, filename):
            yield os.path.abspath(os.path.join(path, filename))


def find_one(path, filename_regex):
    """Find the first file in ``path`` that match ``filename_regex`` regex."""
    for _path in find_all(path, filename_regex):
        return _path
    return ''
