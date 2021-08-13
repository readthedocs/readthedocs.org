"""Audit module."""

import logging

from django.apps import AppConfig

log = logging.getLogger(__name__)


class AuditConfig(AppConfig):
    name = 'readthedocs.audit'

    def ready(self):
        log.info("Importing all Signals handlers")
        import readthedocs.audit.signals  # noqa
