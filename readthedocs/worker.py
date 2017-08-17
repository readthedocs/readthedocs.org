"""Celery worker application instantiation"""

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from django.conf import settings


def create_application():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readthedocs.settings.dev')
    app = Celery('readthedocs')
    app.config_from_object('django.conf:settings')
    app.autodiscover_tasks()
    return app


app = create_application()
