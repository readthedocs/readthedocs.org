"""Celery worker application instantiation"""

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery


def create_application():
    """Create a Celery application using Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readthedocs.settings.dev')
    application = Celery('readthedocs')
    application.config_from_object('django.conf:settings')
    application.autodiscover_tasks(None)
    return application


app = create_application()  # pylint: disable=invalid-name
