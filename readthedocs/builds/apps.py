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
            from readthedocsext.builds.tasks import ShutdownBuilder
            app.tasks.register(ShutdownBuilder)
        except (ModuleNotFoundError, ImportError):
            log.info('ShutdownBuilder task could not be imported.')
