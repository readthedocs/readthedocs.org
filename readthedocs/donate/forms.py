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
            'logo_url',
            'site_url',
            'public',
        )
        labels = {
            'public': _('Make this donation public'),
        }
        help_texts = {
            'public': _('Your name and image will be displayed on the donation page'),
            'email': _('Your email is used for Gravatar and so we can send you a receipt'),
            'logo_url': _("URL of your company's logo, images should be 300x300 pixels or less"),
            'dollars': _('Companies donating over $400 can specify a logo URL and site link'),
        }
        widgets = {
            'dollars': forms.Select(attrs={
                'data-bind': 'value: dollars'
            }),
            'logo_url': forms.TextInput(attrs={
                'data-bind': 'value: logo_url, enable: urls_enabled'
            }),
            'site_url': forms.TextInput(attrs={
                'data-bind': 'value: site_url, enable: urls_enabled'
            })
        }

    last_4_digits = forms.CharField(widget=forms.HiddenInput(), required=True)
    stripe_id = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SupporterForm, self).__init__(*args, **kwargs)

    def clean(self):
        '''Call stripe for payment (not ideal here) and clean up logo < $200'''
        dollars = self.cleaned_data['dollars']
        if dollars < 200:
            self.cleaned_data['logo_url'] = None
            self.cleaned_data['site_url'] = None
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
        if commit and self.user is not None and self.user.is_authenticated():
            supporter.user = self.user
            supporter.save()
        return supporter
