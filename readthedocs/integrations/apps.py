"""Django app configuration for the integrations app."""

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "readthedocs.integrations"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
