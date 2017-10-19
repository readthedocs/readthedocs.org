"""Signals for adding custom context data"""

from __future__ import absolute_import

import django.dispatch

finalize_sphinx_context_data = django.dispatch.Signal(
    providing_args=['buildenv', 'context', 'response_data']
)
