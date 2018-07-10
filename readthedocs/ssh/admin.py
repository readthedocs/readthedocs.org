# -*- coding: utf-8 -*-
"""
Django Admin functions for ssh application.

Register models from ``readthedocs.ssh`` application to be shown in the Django
Admin interface to interact with them.

.. note::

    This functionality is not enabled by default. Views and models from this
    application are not exposed to the user.
"""
from __future__ import division, print_function, unicode_literals

from django.contrib import admin

from .models import SSHKey

admin.site.register(SSHKey)
