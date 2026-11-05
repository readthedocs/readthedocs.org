"""Django configuration for readthedocs.builds application."""

import structlog
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


log = structlog.get_logger(__name__)


class Config(AppConfig):
    name = "readthedocs.builds"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
    label = "builds"
    verbose_name = _("Builds")

    def ready(self):
        import readthedocs.builds.tasks  # noqa
        import readthedocs.builds.signals_receivers  # noqa
