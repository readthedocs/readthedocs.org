"""Build signals."""

import django.dispatch


# Useful to know when to purge the footer
version_changed = django.dispatch.Signal()
