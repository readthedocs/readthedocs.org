"""Forms for RTD donations"""

from __future__ import absolute_import
from builtins import object
import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from readthedocs.payments.forms import StripeModelForm, StripeResourceMixin
from readthedocs.payments.utils import stripe

from .models import Supporter

log = logging.getLogger(__name__)


class SupporterForm(StripeResourceMixin, StripeModelForm):

    """Donation support sign up form

    This extends the basic payment form, giving fields for credit card number,
    expiry, and CVV. The proper Knockout data bindings are established on
    :py:class:`StripeModelForm`
    """

    class Meta(object):
        model = Supporter
        fields = (
            'last_4_digits',
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
            'dollars': forms.HiddenInput(attrs={
                'data-bind': 'value: dollars'
            }),
            'logo_url': forms.TextInput(attrs={
                'data-bind': 'value: logo_url, enable: urls_enabled'
            }),
            'site_url': forms.TextInput(attrs={
                'data-bind': 'value: site_url, enable: urls_enabled'
            }),
            'last_4_digits': forms.TextInput(attrs={
                'data-bind': 'valueInit: card_digits, value: card_digits'
            }),
        }

    last_4_digits = forms.CharField(widget=forms.HiddenInput(), required=True)
    name = forms.CharField(required=True)
    email = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(SupporterForm, self).__init__(*args, **kwargs)

    def validate_stripe(self):
        """Call stripe for payment (not ideal here) and clean up logo < $200"""
        dollars = self.cleaned_data['dollars']
        if dollars < 200:
            self.cleaned_data['logo_url'] = None
            self.cleaned_data['site_url'] = None
        stripe.Charge.create(
            amount=int(self.cleaned_data['dollars']) * 100,
            currency='usd',
            source=self.cleaned_data['stripe_token'],
            description='Read the Docs Sustained Engineering',
            receipt_email=self.cleaned_data['email']
        )

    def save(self, commit=True):
        supporter = super(SupporterForm, self).save(commit)
        if commit and self.user is not None and self.user.is_authenticated():
            supporter.user = self.user
            supporter.save()
        return supporter


class EthicalAdForm(StripeResourceMixin, StripeModelForm):

    """Payment form for ethical ads

    This extends the basic payment form, giving fields for credit card number,
    expiry, and CVV. The proper Knockout data bindings are established on
    :py:class:`StripeModelForm`
    """

    class Meta(object):
        model = Supporter
        fields = (
            'last_4_digits',
            'name',
            'email',
            'dollars',
        )
        help_texts = {
            'email': _('Your email is used so we can send you a receipt'),
        }
        widgets = {
            'dollars': forms.HiddenInput(attrs={
                'data-bind': 'value: dollars'
            }),
            'last_4_digits': forms.TextInput(attrs={
                'data-bind': 'valueInit: card_digits, value: card_digits'
            }),
        }

    last_4_digits = forms.CharField(widget=forms.HiddenInput(), required=True)
    name = forms.CharField(required=True)
    email = forms.CharField(required=True)

    def validate_stripe(self):
        stripe.Charge.create(
            amount=int(self.cleaned_data['dollars']) * 100,
            currency='usd',
            source=self.cleaned_data['stripe_token'],
            description='Read the Docs Sponsorship Payment',
            receipt_email=self.cleaned_data['email']
        )
