"""We define custom Django signals to trigger before executing searches."""
from __future__ import absolute_import
import django.dispatch

before_project_search = django.dispatch.Signal(providing_args=["body"])
before_file_search = django.dispatch.Signal(providing_args=["body"])
before_section_search = django.dispatch.Signal(providing_args=["body"])
