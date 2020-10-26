# -*- coding: utf-8 -*-

"""Payment forms."""

import logging

from django import forms
from django.utils.translation import ugettext_lazy as _
from stripe import Charge, Customer
from stripe.error import InvalidRequestError

from .utils import stripe


log = logging.getLogger(__name__)


class StripeResourceMixin:

    """Stripe actions for resources, available as a Form mixin class."""

    def ensure_stripe_resource(self, resource, attrs):
        try:
            instance = resource.retrieve(attrs['id'])
        except (KeyError, InvalidRequestError):
            try:
                del attrs['id']
            except KeyError:
                pass
            return resource.create(**attrs)
        else:
            for (key, val) in list(attrs.items()):
                setattr(instance, key, val)
            instance.save()
            return instance

    def get_customer_kwargs(self):
        raise NotImplementedError

    def get_customer(self):
        return self.ensure_stripe_resource(
            resource=Customer,
            attrs=self.get_customer_kwargs(),
        )

    def get_subscription_kwargs(self):
        raise NotImplementedError

    def get_subscription(self):
        customer = self.get_customer()
        return self.ensure_stripe_resource(
            resource=customer.subscriptions,
            attrs=self.get_subscription_kwargs(),
        )

    def get_charge_kwargs(self):
        raise NotImplementedError

    def get_charge(self):
        return self.ensure_stripe_resource(
            resource=Charge,
            attrs=self.get_charge_kwargs(),
        )


class StripeModelForm(forms.ModelForm):

    """
    Payment form base for Stripe interaction.

    Use this as a base class for payment forms. It includes the necessary fields
    for card input and manipulates the Knockout field data bindings correctly.

    :cvar stripe_token: Stripe token passed from Stripe.js
    :cvar cc_number: Credit card number field, used only by Stripe.js
    :cvar cc_expiry: Credit card expiry field, used only by Stripe.js
    :cvar cc_cvv: Credit card security code field, used only by Stripe.js
    """

    business_vat_id = forms.CharField(
        label=_('VAT ID number'),
        required=False,
    )

    # Stripe token input from Stripe.js
    stripe_token = forms.CharField(
        required=False,
        widget=forms.HiddenInput(
            attrs={
                'data-bind': 'valueInit: stripe_token',
            },
        ),
    )

    # Fields used for fetching token with javascript, listed as form fields so
    # that data can survive validation errors
    cc_number = forms.CharField(
        label=_('Card number'),
        widget=forms.TextInput(
            attrs={
                'data-bind': (
                    'valueInit: cc_number, '
                    'textInput: cc_number, '
                    '''css: {'field-error': error_cc_number() != null}'''
                ),
            },
        ),
        max_length=25,
        required=False,
    )
    cc_expiry = forms.CharField(
        label=_('Card expiration'),
        widget=forms.TextInput(
            attrs={
                'data-bind': (
                    'valueInit: cc_expiry, '
                    'textInput: cc_expiry, '
                    '''css: {'field-error': error_cc_expiry() != null}'''
                ),
            },
        ),
        max_length=10,
        required=False,
    )
    cc_cvv = forms.CharField(
        label=_('Card CVV'),
        widget=forms.TextInput(
            attrs={
                'data-bind': (
                    'valueInit: cc_cvv, '
                    'textInput: cc_cvv, '
                    '''css: {'field-error': error_cc_cvv() != null}'''
                ),
                'autocomplete': 'off',
            },
        ),
        max_length=8,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)

    def validate_stripe(self):
        """
        Run validation against Stripe.

        This is what will create several objects using the Stripe API. We need
        to actually create the objects, as that is what will provide us with
        validation errors to throw back at the form.

        Form fields can be accessed here via ``self.cleaned_data`` as this
        method is triggered from the :py:meth:`clean` method. Cleaned form data
        should already exist on the form at this point.
        """
        raise NotImplementedError

    def clean_stripe_token(self):
        data = self.cleaned_data['stripe_token']
        if not data:
            data = None
        return data

    def clean(self):
        """
        Clean form to add Stripe objects via API during validation phase.

        This will handle ensuring a customer and subscription exist and will
        raise any issues as validation errors.  This is required because part of
        Stripe's validation happens on the API call to establish a subscription.
        """
        cleaned_data = super().clean()

        # Form isn't valid, no need to try to associate a card now
        if not self.is_valid():
            self.clear_card_data()
            return

        try:
            self.validate_stripe()
        except stripe.error.CardError as e:
            self.clear_card_data()
            field_lookup = {
                'cvc': 'cc_cvv',
                'number': 'cc_number',
                'expiry': 'cc_expiry',
                'exp_month': 'cc_expiry',
                'exp_year': 'cc_expiry',
            }
            error_field = field_lookup.get(e.param)
            self.add_error(
                error_field,
                forms.ValidationError(str(e)),
            )
        except stripe.error.StripeError as e:
            log.exception('There was a problem communicating with Stripe')
            raise forms.ValidationError(
                _('There was a problem communicating with Stripe'),
            )
        return cleaned_data

    def clear_card_data(self):
        """
        Clear card data on validation errors.

        This requires the form was created by passing in a mutable QueryDict
        instance, see :py:class:`readthedocs.payments.mixin.StripeMixin`
        """
        try:
            self.data['stripe_token'] = None
        except AttributeError:
            raise AttributeError(
                'Form was passed immutable QueryDict POST data',
            )

    def fields_with_cc_group(self):
        group = {
            'is_cc_group': True,
            'fields': [],
        }
        for field in self:
            if field.name in ['cc_number', 'cc_expiry', 'cc_cvv']:
                group['fields'].append(field)
            else:
                yield field
        yield group
