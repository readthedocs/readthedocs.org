from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import OnceUser


class SupporterForm(forms.ModelForm):

    class Meta:
        model = OnceUser
        fields = (
            'last_4_digits',
            'stripe_id',
            'name',
            'email',
            'dollars',
            'public',
        )
        labels = {
            'public': _('Make this donation public'),
        }
        help_texts = {
            'public': _('Your name and gravatar will be displayed on the donation page'),
        }

    last_4_digits = forms.CharField(widget=forms.HiddenInput(), required=True)
    stripe_id = forms.CharField(widget=forms.HiddenInput(), required=True)
