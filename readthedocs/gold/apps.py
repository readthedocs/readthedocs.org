from __future__ import absolute_import, division, print_function

from django.apps import AppConfig


class GoldAppConfig(AppConfig):
    name = 'readthedocs.gold'
    verbose_name = 'Gold'

    def ready(self):
        import readthedocs.gold.signals  # noqa
