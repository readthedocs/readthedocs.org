# -*- coding: utf-8 -*-

"""Forms for core app."""

import logging

from django import forms
from django.contrib.auth.models import User
from django.forms.fields import CharField
from django.utils.translation import ugettext_lazy as _

from .models import UserProfile


log = logging.getLogger(__name__)


class UserProfileForm(forms.ModelForm):
    first_name = CharField(label=_('First name'), required=False, max_length=30)
    last_name = CharField(label=_('Last name'), required=False, max_length=30)

    class Meta:
        model = UserProfile
        # Don't allow users edit someone else's user page
        fields = ['first_name', 'last_name', 'homepage']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except AttributeError:
            pass

    def save(self, commit=True):
        first_name = self.cleaned_data.pop('first_name', None)
        last_name = self.cleaned_data.pop('last_name', None)
        profile = super().save(commit=commit)
        if commit:
            user = profile.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        return profile


class UserDeleteForm(forms.ModelForm):
    username = CharField(
        label=_('Username'),
        help_text=_('Please type your username to confirm.'),
    )

    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        data = self.cleaned_data['username']

        if self.instance.username != data:
            raise forms.ValidationError(_('Username does not match!'))

        return data


class UserAdvertisingForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['allow_ads']


class FacetField(forms.MultipleChoiceField):

    """
    For filtering searches on a facet.

    Has validation for the format of facet values.
    """

    def valid_value(self, value):
        """
        Although this is a choice field, no choices need to be supplied.

        Instead, we just validate that the value is in the correct format for
        facet filtering (facet_name:value)
        """
        if ':' not in value:
            return False
        return True
