from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'readthedocs.search'

    def ready(self):
        import readthedocs.search.signals  # noqa
