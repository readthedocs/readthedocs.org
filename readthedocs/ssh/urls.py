# -*- coding: utf-8 -*-

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
