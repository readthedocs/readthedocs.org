"""Celery worker application instantiation."""

import os

from celery import Celery
from django.conf import settings

from django_structlog.celery.steps import DjangoStructLogInitStep


def create_application():
    """Create a Celery application using Django settings."""
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'readthedocs.settings.dev',
    )

    application = Celery(settings.CELERY_APP_NAME)
    application.config_from_object('django.conf:settings')
    application.autodiscover_tasks(None)

    # A step to initialize django-structlog
    application.steps['worker'].add(DjangoStructLogInitStep)

    return application


app = create_application()  # pylint: disable=invalid-name
