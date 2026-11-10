"""Audit module."""

import structlog
from django.apps import AppConfig


log = structlog.get_logger(__name__)


class AuditConfig(AppConfig):
    name = "readthedocs.audit"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import readthedocs.audit.signals  # noqa
