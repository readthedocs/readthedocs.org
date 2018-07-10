# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from readthedocs.constants import pattern_opts

urlpatterns = [
    url((r'^dashboard/(?P<project_slug>{project_slug})/keys/'
         .format(**pattern_opts)),
        include('readthedocs.ssh.urls')),
]
