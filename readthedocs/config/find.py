# -*- coding: utf-8 -*-

"""Helper functions to search files."""

import os
import re


def find_one(path, filename_regex):
    """Find the first file in ``path`` that match ``filename_regex`` regex."""
    _path = os.path.abspath(path)
    for filename in os.listdir(_path):
        if re.match(filename_regex, filename):
            return os.path.join(_path, filename)

    return ''
