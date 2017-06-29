"""App configurations for core app."""

from __future__ import absolute_import
from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    name = 'readthedocs.core'
    verbose_name = 'Core'

    def ready(self):
        import readthedocs.core.signals  # noqa
