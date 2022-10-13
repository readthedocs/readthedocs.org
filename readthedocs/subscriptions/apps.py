"""Subscriptions app."""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    name = 'readthedocs.subscriptions'
    label = 'subscriptions'

    def ready(self):
        import readthedocs.subscriptions.event_handlers  # noqa
        import readthedocs.subscriptions.signals  # noqa
        import readthedocs.subscriptions.tasks  # noqa

        self._add_custom_manager()

    # pylint: disable=no-self-use
    def _add_custom_manager(self):
        from djstripe.models import Subscription

        from readthedocs.subscriptions.querysets import StripeSubscriptionQueryset

        manager = StripeSubscriptionQueryset.as_manager()
        manager.contribute_to_class(Subscription, "rtd")
