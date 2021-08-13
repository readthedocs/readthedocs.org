# -*- coding: utf-8 -*-

"""Signals for adding custom context data."""

import django.dispatch


finalize_sphinx_context_data = django.dispatch.Signal(
    providing_args=['buildenv', 'context', 'response_data'],
)
