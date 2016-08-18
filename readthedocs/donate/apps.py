"""Donate app config for establishing signals"""

import logging

from django.apps import AppConfig

log = logging.getLogger(__name__)


class DonateAppConfig(AppConfig):
    name = 'readthedocs.donate'
    verbose_name = 'Donate'

    def ready(self):
        import readthedocs.donate.signals  # noqa
