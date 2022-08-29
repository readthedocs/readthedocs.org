"""Custom domains application."""

from django.apps import AppConfig


class DomainsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.domains"

    def ready(self):
        import readthedocs.domains.tasks  # noqa
