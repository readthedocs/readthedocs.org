"""
Telemetry application.

Collect relevant data to be analyzed later.
"""

from django.apps import AppConfig


class TelemetryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.telemetry"

    def ready(self):
        import readthedocs.telemetry.tasks  # noqa
