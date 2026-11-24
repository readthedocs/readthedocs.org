"""Organizations app."""

from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "readthedocs.organizations"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import readthedocs.organizations.signals  # noqa
