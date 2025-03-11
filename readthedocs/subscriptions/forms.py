"""Subscriptions forms."""

from django import forms
from django.utils.translation import gettext_lazy as _
from djstripe import models as djstripe

from readthedocs.subscriptions.products import get_listed_products


class PlanForm(forms.Form):
    """Form to create a subscription after the previous one has ended."""

    plan = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        products_id = [product.stripe_id for product in get_listed_products()]
        stripe_prices = (
            djstripe.Price.objects.filter(product__id__in=products_id, active=True)
            .select_related("product")
            .order_by("unit_amount")
        )
        self.fields["plan"].choices = [
            (price.id, f"{price.product.name} ({price.human_readable_price})")
            for price in stripe_prices
        ]
        self.fields["plan"].help_text = _(
            'Check our <a href="https://about.readthedocs.com/pricing/">pricing page</a> '
            "for more information about each plan."
        )
