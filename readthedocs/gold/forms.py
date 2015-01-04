from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from .models import LEVEL_CHOICES


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

    def addError(self, message):
        self._errors[NON_FIELD_ERRORS] = self.error_class([message])
