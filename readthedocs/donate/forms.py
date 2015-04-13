import logging

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import stripe

from .models import Supporter

log = logging.getLogger(__name__)


class SupporterForm(forms.ModelForm):

    class Meta:
        model = Supporter
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SupporterForm, self).__init__(*args, **kwargs)

    def clean(self):
        try:
            stripe.api_key = settings.STRIPE_SECRET
            stripe.Charge.create(
                amount=int(self.cleaned_data['dollars']) * 100,
                currency='usd',
                source=self.cleaned_data['stripe_id'],
                description='Read the Docs Sustained Engineering',
                receipt_email=self.cleaned_data['email']
            )
        except stripe.error.CardError, e:
            stripe_error = e.json_body['error']
            log.error('Credit card error: %s', stripe_error['message'])
            raise forms.ValidationError(
                _('There was a problem processing your card: %(message)s'),
                params=stripe_error)
        return self.cleaned_data

    def save(self, commit=True):
        supporter = super(SupporterForm, self).save(commit)
        if commit:
            supporter.user = self.user
            supporter.save()
        return supporter
