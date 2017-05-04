from __future__ import absolute_import, division, print_function

import django.dispatch

before_project_search = django.dispatch.Signal(providing_args=["body"])
before_file_search = django.dispatch.Signal(providing_args=["body"])
before_section_search = django.dispatch.Signal(providing_args=["body"])
