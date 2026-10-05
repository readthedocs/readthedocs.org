from unittest import mock

import pytest
from django.core.exceptions import SuspiciousFileOperation, SuspiciousOperation
from django.test import TestCase

from readthedocs.storage.s3_storage import RTDS3Storage


class TestRTDS3Storage(TestCase):

    def setUp(self):
        self.storage = RTDS3Storage()

    def test_delete_directory(self):
        mock_bucket = mock.MagicMock()
        self.storage._bucket = mock_bucket
        self.storage.delete_directory("projects/my-project/en/latest/")
        mock_bucket.objects.filter.assert_called_once_with(
            Prefix="projects/my-project/en/latest/"
        )
        mock_bucket.objects.filter.return_value.delete.assert_called_once()

    def test_delete_directory_adds_trailing_slash(self):
        mock_bucket = mock.MagicMock()
        self.storage._bucket = mock_bucket
        self.storage.delete_directory("projects/my-project/en/latest")
        mock_bucket.objects.filter.assert_called_once_with(
            Prefix="projects/my-project/en/latest/"
        )
        mock_bucket.objects.filter.return_value.delete.assert_called_once()

    def test_delete_directory_raises_for_root_path(self):
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("/")

    def test_delete_directory_raises_for_empty_path(self):
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("")

    def test_delete_directory_raises_for_root_path_with_location(self):
        self.storage.location = "projects"
        with pytest.raises(SuspiciousOperation):
            self.storage.delete_directory("/")

    def test_delete_directory_raises_for_empty_path_with_location(self):
        self.storage.location = "projects"
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("")

    def test_delete_paths(self):
        mock_bucket = mock.MagicMock()
        self.storage._bucket = mock_bucket
        self.storage.delete_paths(["one.txt", "another-path/two.txt", "projects/my-project/en/latest/index.html"])
        mock_bucket.delete_objects.assert_called_once_with(
            Delete={
                "Objects": [
                    {"Key": "one.txt"},
                    {"Key": "another-path/two.txt"},
                    {"Key": "projects/my-project/en/latest/index.html"},
                ],
                "Quiet": True,
            }
        )

    def test_generate_presigned_post(self):
        mock_bucket = mock.MagicMock()
        self.storage._bucket = mock_bucket
        self.storage.bucket_name = "my-bucket"
        self.storage.default_acl = "private"
        mock_client = mock_bucket.meta.client
        mock_client.generate_presigned_post.return_value = {
            "url": "https://my-bucket.s3.amazonaws.com/",
            "fields": {},
        }

        response = self.storage.generate_presigned_post(
            key="projects/my-project/en/latest/artifact.zip",
            content_type="application/zip",
        )

        mock_client.generate_presigned_post.assert_called_once_with(
            Bucket="my-bucket",
            Key="projects/my-project/en/latest/artifact.zip",
            Fields={
                "bucket": "my-bucket",
                "acl": "private",
                "Content-Type": "application/zip",
            },
            Conditions=[
                {"bucket": "my-bucket"},
                {"acl": "private"},
                {"Content-Type": "application/zip"},
                ["content-length-range", 1, 1024 * 1024 * 1024],
            ],
            ExpiresIn=3600,
        )
        assert response == {
            "url": "https://my-bucket.s3.amazonaws.com/",
            "fields": {},
        }

    def test_generate_presigned_post_custom_options(self):
        mock_bucket = mock.MagicMock()
        self.storage._bucket = mock_bucket
        self.storage.bucket_name = "my-bucket"
        self.storage.default_acl = "private"
        mock_client = mock_bucket.meta.client

        self.storage.generate_presigned_post(
            key="projects/my-project/en/latest/artifact.zip",
            content_type="application/zip",
            expires_in=60,
            min_size=10,
            max_size=2048,
        )

        mock_client.generate_presigned_post.assert_called_once_with(
            Bucket="my-bucket",
            Key="projects/my-project/en/latest/artifact.zip",
            Fields={
                "bucket": "my-bucket",
                "acl": "private",
                "Content-Type": "application/zip",
            },
            Conditions=[
                {"bucket": "my-bucket"},
                {"acl": "private"},
                {"Content-Type": "application/zip"},
                ["content-length-range", 10, 2048],
            ],
            ExpiresIn=60,
        )
