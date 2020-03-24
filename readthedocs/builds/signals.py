# -*- coding: utf-8 -*-

"""Build signals."""

import logging
import os

from django.conf import settings
from django.dispatch import receiver, Signal
from django.utils.autoreload import file_changed

from readthedocs.worker import app

build_complete = Signal(providing_args=['build'])


log = logging.getLogger(__file__)


if all([
        # restart workers in local docker compose only
        settings.RTD_DOCKER_COMPOSE,
        # restart workers only from web instance
        os.environ['DJANGO_SETTINGS_MODULE'].endswith('web_docker'),
]):
    @receiver(file_changed)
    def restart_celery_workers(*args, **kwargs):
        log.info('Restarting celery workers')
        app.control.broadcast('pool_restart', arguments={'reload': True})
