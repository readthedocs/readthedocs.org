# -*- coding: utf-8 -*-

"""App configurations for core app."""

from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    name = 'readthedocs.core'
    verbose_name = 'Core'

    def ready(self):
        import readthedocs.core.signals  # noqa

        # Import `readthedocs.core.logs` to set up structlog
        import readthedocs.core.logs  # noqa

        try:
            import readthedocsext.monitoring.metrics.tasks
        except (ModuleNotFoundError, ImportError):
            log.info('Metrics tasks could not be imported.')
