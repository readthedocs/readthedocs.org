# -*- coding: utf-8 -*-

"""Celery worker application instantiation."""

import os

from celery import Celery
from django.conf import settings


def create_application():
    """Create a Celery application using Django settings."""
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'readthedocs.settings.dev',
    )

    application = Celery(settings.CELERY_APP_NAME)
    application.config_from_object('django.conf:settings')
    application.autodiscover_tasks(None)
    return application


app = create_application()  # pylint: disable=invalid-name
