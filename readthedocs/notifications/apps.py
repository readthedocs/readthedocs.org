"""Django app configuration for the notifications app."""

from django.apps import AppConfig


class NotificationsAppConfig(AppConfig):
    name = "readthedocs.notifications"
    verbose_name = "Notifications"

    def ready(self):
        import readthedocs.notifications.signals  # noqa
