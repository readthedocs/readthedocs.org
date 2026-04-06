from unittest import mock

from django.test import TestCase

from readthedocs.storage.s3_storage import RTDS3Storage


class TestS3BuildMediaStorageDeleteDirectory(TestCase):

    def setUp(self):
        self.storage = RTDS3Storage()

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
