"""URL configuration for core app."""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.constants import pattern_opts
from readthedocs.core import views


core_urls = [
    # Random other stuff
    url(
        (
            r'^wipe/(?P<project_slug>{project_slug})/'
            r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)
        ),
        views.wipe_version,
        name='wipe_version',
    ),
]
