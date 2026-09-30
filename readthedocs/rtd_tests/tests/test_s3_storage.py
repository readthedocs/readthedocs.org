import io
from unittest import mock

import pytest
from botocore.exceptions import ClientError

from readthedocs.storage.s3_storage import RTDS3Storage


def _client_error(status):
    return ClientError(
        {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": status}},
        "GetObject",
    )


class TestRTDS3StorageReadFile:
    def _storage(self):
        storage = RTDS3Storage(bucket_name="bucket")
        storage._bucket = mock.MagicMock()
        return storage

    def test_read_file_uses_a_single_get(self):
        storage = self._storage()
        obj = storage._bucket.Object.return_value
        obj.get.return_value = {"Body": io.BytesIO(b"<html>hi</html>")}

        assert storage.read_file("html/project/latest/index.html") == b"<html>hi</html>"

        storage._bucket.Object.assert_called_once_with("html/project/latest/index.html")
        obj.get.assert_called_once_with()
        # No HeadObject before the download.
        obj.load.assert_not_called()
        obj.download_fileobj.assert_not_called()

    def test_read_file_missing(self):
        storage = self._storage()
        storage._bucket.Object.return_value.get.side_effect = _client_error(404)

        with pytest.raises(FileNotFoundError):
            storage.read_file("html/project/latest/missing.html")

    def test_read_file_other_errors_propagate(self):
        storage = self._storage()
        storage._bucket.Object.return_value.get.side_effect = _client_error(403)

        with pytest.raises(ClientError):
            storage.read_file("html/project/latest/index.html")
