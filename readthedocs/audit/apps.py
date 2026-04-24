"""Audit module."""

import structlog
from django.apps import AppConfig


log = structlog.get_logger(__name__)


class AuditConfig(AppConfig):
    name = "readthedocs.audit"

    def ready(self):
        import readthedocs.audit.signals  # noqa
