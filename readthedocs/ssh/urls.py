# -*- coding: utf-8 -*-
"""
URLs for SSH key management under Project Admin tab.

.. note::

    This URLs should be included by prepending the ``project_slug`` regex
    otherwise they won't work since they depend on a project.
"""
from __future__ import division, print_function, unicode_literals

from django.conf.urls import url

from .views import (
    DeleteKeysView, DetailKeysView, GenerateKeysView, ListKeysView,
    UploadKeysView)

urlpatterns = [
    url(
        r'^$',
        ListKeysView.as_view(),
        name='projects_keys',
    ),
    url(
        r'^generate/$',
        GenerateKeysView.as_view(),
        name='projects_keys_generate',
    ),
    url(
        r'^upload/$',
        UploadKeysView.as_view(),
        name='projects_keys_upload',
    ),
    url(
        r'^(?P<key_pk>\d+)/$',
        DetailKeysView.as_view(),
        name='projects_keys_detail',
    ),
    url(
        r'^(?P<key_pk>\d+)/delete/$',
        DeleteKeysView.as_view(),
        name='projects_keys_delete',
    ),
]
