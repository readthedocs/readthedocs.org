"""App configurations for core app."""

import structlog
from django.apps import AppConfig


log = structlog.get_logger(__name__)


class CoreAppConfig(AppConfig):
    name = "readthedocs.core"
    verbose_name = "Core"

    def ready(self):
        # Import `readthedocs.core.logs` to set up structlog
        import readthedocs.core.logs  # noqa
        import readthedocs.core.signals  # noqa

        try:
            import readthedocsext.monitoring.metrics.tasks  # noqa
        except (ModuleNotFoundError, ImportError):
            log.info("Metrics tasks could not be imported.")
