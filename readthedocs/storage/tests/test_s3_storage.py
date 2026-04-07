from unittest import mock

import pytest
from django.core.exceptions import SuspiciousFileOperation
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
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("/")

    def test_delete_directory_raises_for_empty_path_with_location(self):
        self.storage.location = "projects"
        with pytest.raises(SuspiciousFileOperation):
            self.storage.delete_directory("")
