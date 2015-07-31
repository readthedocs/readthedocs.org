from django import forms

from .models import LEVEL_CHOICES, GoldUser


class CardForm(forms.Form):

    last_4_digits = forms.CharField(
        required=True,
        min_length=4,
        max_length=4,
        widget=forms.HiddenInput()
    )

    stripe_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    level = forms.ChoiceField(
        required=True,
        choices=LEVEL_CHOICES,
    )


class GoldProjectForm(forms.Form):
    project = forms.CharField(
        required=True,
    )
