from __future__ import absolute_import, division, print_function

import django.dispatch

footer_response = django.dispatch.Signal(
    providing_args=["request", "context", "response_data"]
)
