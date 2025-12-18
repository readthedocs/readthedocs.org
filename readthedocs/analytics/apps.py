"""Django app config for the analytics app."""

from django.apps import AppConfig


class AnalyticsAppConfig(AppConfig):
    """Analytics app init code."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.analytics"
    verbose_name = "Analytics"

    def ready(self):
        """Initialize OpenTelemetry when app is ready."""
        from readthedocs.analytics.telemetry import analytics_metrics

        analytics_metrics.initialize()
