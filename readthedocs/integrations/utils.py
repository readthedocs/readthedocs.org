"""Integration utility functions."""

from __future__ import division, print_function, unicode_literals

import json
import os


def normalize_request_payload(request_body, content_type):
    """
    Normalize the request body, hopefully to JSON.

    This will attempt to return a JSON body.

    :param request_body: String representing the request's body
    :param content_type: The content type of the request
    :returns: A Python object representing the request_body
    """
    if content_type != 'application/json':
        raise NotImplementedError
    return json.loads(request_body)


def get_secret(size=64):
    """
    Get a random string of `size` bytes.

    :param size: Number of bytes
    """
    return os.urandom(size).hex()
