"""Django app configuration for the notifications app."""

from django.apps import AppConfig


class NotificationsAppConfig(AppConfig):
    name = "readthedocs.notifications"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Notifications"

    def ready(self):
        import readthedocs.notifications.signals  # noqa
