"""Django app config for the analytics app."""

from django.apps import AppConfig


class AnalyticsAppConfig(AppConfig):
    """Analytics app init code."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.analytics"
    verbose_name = "Analytics"
