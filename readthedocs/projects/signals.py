"""Project signals."""

import django.dispatch

before_vcs = django.dispatch.Signal()

before_build = django.dispatch.Signal()
after_build = django.dispatch.Signal()

project_import = django.dispatch.Signal()

# Used to purge files from the CDN
files_changed = django.dispatch.Signal()
