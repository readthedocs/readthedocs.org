# -*- coding: utf-8 -*-
"""Celery worker application instantiation"""

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

from readthedocs.core.utils.extend import SettingsOverrideObject


class CeleryAppBase(object):

    def create(self):
        """Create a Celery application using Django settings"""
        os.environ.setdefault(
            'DJANGO_SETTINGS_MODULE',
            'readthedocs.settings.dev',
        )

        application = Celery('readthedocs')
        application.config_from_object('django.conf:settings')
        application.autodiscover_tasks(None)
        return application


class CeleryApp(SettingsOverrideObject):
    _default_class = CeleryAppBase


app = CeleryApp().create()
