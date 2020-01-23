from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest


class MockStorageMixin:

    def tearDown(self):
        super().tearDown()
        BuildMediaFileSystemStorageTest._existing_files = []

    def _storage_exists(self, files):
        BuildMediaFileSystemStorageTest._existing_files = files
