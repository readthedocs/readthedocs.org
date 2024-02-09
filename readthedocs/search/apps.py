from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "readthedocs.search"

    def ready(self):
        import readthedocs.search.signals  # noqa
