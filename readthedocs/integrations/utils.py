"""Integration utility functions."""

from __future__ import division, print_function, unicode_literals

import json
import os


def normalize_request_payload(request_body, content_type):
    """
    Normalize the request body, hopefully to JSON.

    This will attempt to return a JSON body, backing down to a string body next.

    :param request: HTTP request object
    :type request: django.http.HttpRequest
    :returns: The request body as a string
    :rtype: str
    """
    if content_type != 'application/json':
        # Here, request_body can be a dict or a MergeDict. Probably best to
        # normalize everything first
        raise NotImplementedError
    return json.loads(request_body)


def get_secret(size=64):
    return os.urandom(size).hex()
