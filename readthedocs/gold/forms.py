"""Gold subscription forms."""

from __future__ import absolute_import
from builtins import object
from django import forms

from stripe.error import InvalidRequestError
from readthedocs.payments.forms import StripeModelForm, StripeResourceMixin

from .models import LEVEL_CHOICES, GoldUser


class GoldSubscriptionForm(StripeResourceMixin, StripeModelForm):

    """
    Gold subscription payment form.

    This extends the common base form for handling Stripe subscriptions. Credit
    card fields for card number, expiry, and CVV are extended from
    :py:class:`StripeModelForm`, with additional methods from
    :py:class:`StripeResourceMixin` for common operations against the Stripe API.
    """

    class Meta(object):
        model = GoldUser
        fields = ['last_4_digits', 'level']

    last_4_digits = forms.CharField(
        required=True,
        min_length=4,
        max_length=4,
        widget=forms.HiddenInput(attrs={
            'data-bind': 'valueInit: card_digits, value: card_digits'
        })
    )

    level = forms.ChoiceField(
        required=True,
        choices=LEVEL_CHOICES,
    )

    def clean(self):
        self.instance.user = self.customer
        return super(GoldSubscriptionForm, self).clean()

    def validate_stripe(self):
        subscription = self.get_subscription()
        self.instance.stripe_id = subscription.customer
        self.instance.subscribed = True

    def get_customer_kwargs(self):
        return {
            'description': self.customer.get_full_name() or self.customer.username,
            'email': self.customer.email,
            'id': self.instance.stripe_id or None
        }

    def get_subscription(self):
        customer = self.get_customer()
        try:
            # TODO get the first sub more intelligently
            subscriptions = customer.subscriptions.all(limit=5)
            subscription = subscriptions.data[0]
            subscription.plan = self.cleaned_data['level']
            if 'stripe_token' in self.cleaned_data:
                subscription.source = self.cleaned_data['stripe_token']
            subscription.save()
            return subscription
        except (InvalidRequestError, AttributeError, IndexError):
            subscription = customer.subscriptions.create(
                plan=self.cleaned_data['level'],
                source=self.cleaned_data['stripe_token']
            )
            return subscription

    def clear_card_data(self):
        super(GoldSubscriptionForm, self).clear_card_data()
        self.data['last_4_digits'] = None


class GoldProjectForm(forms.Form):
    project = forms.CharField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.projects = kwargs.pop('projects', None)
        super(GoldProjectForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(GoldProjectForm, self).clean()
        if self.projects.count() < self.user.num_supported_projects:
            return cleaned_data
        else:
            self.add_error(
                None, 'You already have the max number of supported projects.')
