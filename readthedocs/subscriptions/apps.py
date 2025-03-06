"""Subscriptions app."""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    """App configuration."""

    name = "readthedocs.subscriptions"
    label = "subscriptions"

    def ready(self):
        import readthedocs.subscriptions.event_handlers  # noqa
        import readthedocs.subscriptions.signals  # noqa
        import readthedocs.subscriptions.tasks  # noqa

        self._add_custom_manager()

    def _add_custom_manager(self):
        """
        Add a custom manager to the djstripe Subscription model.

        Patching the model directly isn't recommended,
        since there may be an additional setup
        done by django when adding a manager.
        Using django's contribute_to_class is the recommended
        way of adding a custom manager to a third party model.

        The new manager will be accessible from ``Subscription.readthedocs``.
        """
        from djstripe.models import Subscription

        from readthedocs.subscriptions.querysets import StripeSubscriptionQueryset

        manager = StripeSubscriptionQueryset.as_manager()
        manager.contribute_to_class(Subscription, "readthedocs")
