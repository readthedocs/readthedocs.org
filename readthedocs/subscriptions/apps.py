"""Subscriptions app."""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    name = 'readthedocs.subscriptions'
    label = 'subscriptions'

    def ready(self):
        import readthedocs.subscriptions.signals  # noqa
