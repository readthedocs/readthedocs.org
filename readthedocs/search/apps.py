"""Project app config"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'readthedocs.search'

    def ready(self):
        from .signals import index_html_file, remove_html_file
