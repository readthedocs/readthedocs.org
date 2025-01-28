"""Organizations app."""

from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "readthedocs.organizations"

    def ready(self):
        import readthedocs.organizations.signals  # noqa
