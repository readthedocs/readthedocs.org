# -*- coding: utf-8 -*-
"""
URLs for SSH key listing over API.

.. note::

    To define these URLs under a project, this line has to be included in a
   ``urlpatterns`` loaded at start up:

        url(r'^api/v2/', include('readthedocs.ssh.restapi.urls')),
"""

from __future__ import division, print_function, unicode_literals


from django.conf.urls import url, include
from rest_framework import routers

from .model_views import ProjectSSHKeyViewSet

# HACK: define new API endpoints under an existing path registered by DRF at
# ``/project/<pk>/``. Instead of re-defining all of the views/endpoints we
# filter the URLs returned by the router and only add the ones we want.
urls = []
router = routers.DefaultRouter()
router.register(r'project', ProjectSSHKeyViewSet, base_name='project')
for routed_url in router.urls:
    if routed_url.name == 'project-keys':
        urls.append(routed_url)

urlpatterns = [
    url(r'^', include(urls)),
]
