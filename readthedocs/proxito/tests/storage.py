"""
Helper Django Storage class to use in El Proxito tests.
"""

from readthedocs.builds.storage import BuildMediaFileSystemStorage


class BuildMediaStorageTest(BuildMediaFileSystemStorage):

    """
    Storage to use in El Proxito tests to have more control.

    Allow to specify when to return ``True`` or ``False`` depending if the file
    does exist or not in the storage backend.

    Mocking ``get_storage_class`` is not always an option, since there are other
    methods that should keep working normally (``.url()``) and not be mocked.
    """

    _existing_files = []

    def exists(self, path):
        if path in self._existing_files:
            return True

        return False
