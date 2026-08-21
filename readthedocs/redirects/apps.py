"""Redirects app config."""

from django.apps import AppConfig


class RedirectsConfig(AppConfig):
    name = "readthedocs.redirects"

    def ready(self):
        import readthedocs.redirects.signals  # noqa
