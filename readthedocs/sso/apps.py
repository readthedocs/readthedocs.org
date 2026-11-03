"""Single Sign On (SSO) app."""

from django.apps import AppConfig


class SsoConfig(AppConfig):
    name = "readthedocs.sso"
    # Existing models use AutoField, see DEFAULT_AUTO_FIELD in settings.
    default_auto_field = "django.db.models.AutoField"
