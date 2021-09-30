# -*- coding: utf-8 -*-

"""Payment view mixin classes."""

from django.conf import settings


class StripeMixin:

    """Adds Stripe publishable key to the context data."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_publishable'] = settings.STRIPE_PUBLISHABLE
        return context
