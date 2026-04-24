"""Payment view mixin classes."""

from djstripe.enums import APIKeyType
from djstripe.models import APIKey


class StripeMixin:
    """Adds Stripe publishable key to the context data."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_publishable"] = (
            APIKey.objects.filter(type=APIKeyType.publishable).first().secret
        )
        return context
