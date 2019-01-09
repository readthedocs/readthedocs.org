# -*- coding: utf-8 -*-

"""Django app configuration for the Gold Membership app."""

from django.apps import AppConfig


class GoldAppConfig(AppConfig):
    name = 'readthedocs.gold'
    verbose_name = 'Gold'

    def ready(self):
        import readthedocs.gold.signals  # noqa
