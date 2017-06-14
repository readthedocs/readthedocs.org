"""URL configuration for comments app."""

from __future__ import absolute_import
from django.conf.urls import url

from readthedocs.comments import views

urlpatterns = [
    url(r'build', views.build, name='build'),
    url(r'_has_node', views.has_node, name='has_node'),
    url(r'_add_node', views.add_node, name='add_node'),
    url(r'_update_node', views.update_node, name='update_node'),
    url(r'_attach_comment', views.attach_comment, name='attach_comment'),
    url(r'_get_metadata', views.get_metadata, name='get_metadata'),
    url(r'_get_options', views.get_options, name='get_options'),
    url(r'(?P<file>.*)', views.serve_file, name='serve_file'),
]
