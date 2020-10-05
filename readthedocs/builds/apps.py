from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class Config(AppConfig):
    name = 'readthedocs.builds'
    label = 'builds'
    verbose_name = _("Builds")

    def ready(self):
        from readthedocs.builds.tasks import ArchiveBuilds
        from readthedocs.worker import app
        app.tasks.register(ArchiveBuilds)
