"""Build signals."""

import django.dispatch


build_complete = django.dispatch.Signal(providing_args=['build'])
# Useful to know when to purge the footer
version_changed = django.dispatch.Signal(providing_args=['version'])
