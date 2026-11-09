from django.apps import AppConfig


class V3Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "API V3"
    name = "readthedocs.api.v3"
