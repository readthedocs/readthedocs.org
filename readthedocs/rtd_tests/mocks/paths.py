"""Context managers to patch os.path.exists calls."""
import os
from unittest import mock


def fake_paths(check):
    """
    Usage:

    >>> with fake_paths(lambda path: True if path.endswith('.pdf') else None):
    ...     assert os.path.exists('my.pdf')
    ...     assert os.path.exists('Nopdf.txt')

    The first assertion will be ok, the second assertion is not faked as the
    ``check`` returned ``None`` for this path.
    """
    original_exists = os.path.exists

    def patched_exists(path):
        result = check(path)
        if result is None:
            return original_exists(path)
        return result

    return mock.patch.object(os.path, "exists", patched_exists)


def fake_paths_lookup(path_dict):
    """
    Usage:

    >>> paths = {'my.txt': True, 'no.txt': False}
    >>> with fake_paths_lookup(paths):
    ...     assert os.path.exists('my.txt') == True
    ...     assert os.path.exists('no.txt') == False
    """

    def check(path):
        return path_dict.get(path, None)

    return fake_paths(check)
