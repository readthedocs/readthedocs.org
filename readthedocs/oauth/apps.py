"""OAuth app config."""

from django.apps import AppConfig


class OAuthConfig(AppConfig):
    name = "readthedocs.oauth"

    def ready(self):
        import readthedocs.oauth.signals  # noqa
