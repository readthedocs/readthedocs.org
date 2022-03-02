"""Subscriptions forms."""

from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from readthedocs.subscriptions.models import Plan


class PlanForm(forms.Form):

    """Form to create a subscription after the previous one has ended."""

    plan = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].choices = [
            (plan.pk, f'{plan.name} (${plan.price})')
            for plan in Plan.objects.filter(published=True).order_by('price')
        ]
        pricing_page = reverse('pricing')
        self.fields['plan'].help_text = _(
            f'Check our <a href="{pricing_page}">pricing page</a> '
            'for more information about each plan.'
        )
