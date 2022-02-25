import structlog

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

log = structlog.get_logger(__name__)


class Config(AppConfig):
    name = 'readthedocs.builds'
    label = 'builds'
    verbose_name = _("Builds")

    def ready(self):
        from readthedocs.builds.tasks import ArchiveBuilds
        from readthedocs.worker import app
        app.tasks.register(ArchiveBuilds)

        try:
            from readthedocsext.monitoring.metrics.tasks import (
                Metrics1mTask,
                Metrics5mTask,
                Metrics10mTask,
                Metrics30mTask,
            )
            app.tasks.register(Metrics1mTask)
            app.tasks.register(Metrics5mTask)
            app.tasks.register(Metrics10mTask)
            app.tasks.register(Metrics30mTask)
        except (ModuleNotFoundError, ImportError):
            log.warning('Metrics tasks could not be imported.')
