import os
import mock


def fake_paths(*paths):
    """
    Returns a context manager that patches ``os.path.exists`` to return
    ``True`` for the given ``paths``.
    """

    original_exists = os.path.exists

    def patched_exists(path):
        if path in paths:
            return True
        return original_exists(path)

    return mock.patch.object(os.path, 'exists', patched_exists)
