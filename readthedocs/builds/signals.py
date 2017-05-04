"""Build signals"""
from __future__ import absolute_import, division, print_function

import django.dispatch


build_complete = django.dispatch.Signal(providing_args=['build'])
