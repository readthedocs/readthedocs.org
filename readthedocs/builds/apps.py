import logging

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)


class Config(AppConfig):
    name = 'readthedocs.builds'
    label = 'builds'
    verbose_name = _("Builds")

    def ready(self):
        from readthedocs.builds.tasks import ArchiveBuilds
        from readthedocs.worker import app
        app.tasks.register(ArchiveBuilds)

        try:
            from readthedocsext.builds.tasks import ShutdownBuilder, StopBuilder
            app.tasks.register(ShutdownBuilder)
            app.tasks.register(StopBuilder)
        except (ModuleNotFoundError, ImportError):
            log.info('ShutdownBuilder/StopBuilder task could not be imported.')

        try:
            from readthedocsext.monitoring.scaling import AutoscaleBuildersTask
            app.tasks.register(AutoscaleBuildersTask)
        except (ModuleNotFoundError, ImportError):
            log.info('AutoscaleBuildersTask task could not be imported.')

        try:
            from readthedocsext.monitoring.metrics.tasks import (
                Metrics1mTask,
                Metrics5mTask,
                Metrics10mTask,
            )
            app.tasks.register(Metrics1mTask)
            app.tasks.register(Metrics5mTask)
            app.tasks.register(Metrics10mTask)
        except (ModuleNotFoundError, ImportError):
            log.info('Metrics tasks could not be imported.')
