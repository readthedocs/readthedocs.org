from readthedocs.proxito.tests.storage import BuildMediaStorageTest


class MockStorageMixin:

    """
    Mixin to controls ``BuildMediaStorageTests.exists`` method.

    This mixin provides a helper to update which files does exist in the storage
    backend and reset them to an empty list on tear down.
    """

    def tearDown(self):
        super().tearDown()
        BuildMediaStorageTest._existing_files = []

    def _storage_exists(self, files):
        BuildMediaStorageTest._existing_files = files
