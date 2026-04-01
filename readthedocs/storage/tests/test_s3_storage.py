from unittest import mock

import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.test import TestCase, override_settings


@override_settings(
    S3_MEDIA_STORAGE_BUCKET="readthedocs-test",
)
class TestS3BuildMediaStorageDeleteDirectory(TestCase):
    def setUp(self):
        from readthedocs.storage.s3_storage import S3BuildMediaStorage

        self.storage = S3BuildMediaStorage()
        self.mock_bucket = mock.MagicMock()
        # Override the internal _bucket attribute (used by the bucket property)
        self.storage._bucket = self.mock_bucket

    def test_delete_directory(self):
        self.storage.delete_directory("projects/my-project/en/latest/")
        self.mock_bucket.objects.filter.assert_called_once_with(
            Prefix="projects/my-project/en/latest/"
        )
        self.mock_bucket.objects.filter.return_value.delete.assert_called_once()

    def test_delete_directory_adds_trailing_slash(self):
        self.storage.delete_directory("projects/my-project/en/latest")
        self.mock_bucket.objects.filter.assert_called_once_with(
            Prefix="projects/my-project/en/latest/"
        )
        self.mock_bucket.objects.filter.return_value.delete.assert_called_once()

    def test_delete_directory_raises_for_root_path(self):
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("/")

    def test_delete_directory_raises_for_empty_path(self):
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("")
