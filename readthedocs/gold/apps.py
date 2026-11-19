"""Django app configuration for the Gold membership app."""

from django.apps import AppConfig


class GoldAppConfig(AppConfig):
    name = "readthedocs.gold"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Gold"

    def ready(self):
        import readthedocs.gold.signals  # noqa
