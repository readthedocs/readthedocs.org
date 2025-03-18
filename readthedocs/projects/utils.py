"""Utility functions used by projects."""

import csv

import structlog
from django.http import StreamingHttpResponse


log = structlog.get_logger(__name__)


class Echo:
    """
    A class that implements just the write method of the file-like interface.

    This class can be used for generating StreamingHttpResponse.
    See: https://docs.djangoproject.com/en/2.2/howto/outputting-csv/#streaming-large-csv-files
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def get_csv_file(filename, csv_data):
    """Get a CSV file to be downloaded as an attachment."""
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in csv_data),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
