"""Django app configuration for the redirects app."""

from django.apps import AppConfig


class RedirectsConfig(AppConfig):
    name = "readthedocs.redirects"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
