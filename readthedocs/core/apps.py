"""Core application config for establishing signals"""

from django.apps import AppConfig


class GoldAppConfig(AppConfig):
    name = 'readthedocs.core'
    verbose_name = 'Core'

    def ready(self):
        if hasattr(self, 'already_run'):
            return
        self.already_run = True
        import readthedocs.core.signals  # noqa
