"""OAuth app config."""

from django.apps import AppConfig


class OAuthConfig(AppConfig):
    name = "readthedocs.oauth"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import readthedocs.oauth.signals  # noqa
