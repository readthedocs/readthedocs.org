# -*- coding: utf-8 -*-
"""Project signals"""

from __future__ import absolute_import
import django.dispatch


before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])

files_changed = django.dispatch.Signal(providing_args=["project", "files"])
